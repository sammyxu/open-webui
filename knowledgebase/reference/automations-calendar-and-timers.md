# Automations, Calendar and Timers

## At a Glance

- An **automation** is a saved prompt that a chosen model runs on a schedule (an iCalendar
  recurrence rule). Each run starts a **new chat** named after the automation (optionally in one of
  the owner's folders) or posts into a **channel**. People create, edit, pause, run now, clone,
  import, export and delete their own automations at `/automations`; nobody else, admins included,
  can open them.
- Access needs the site switch **Automations** (on in code) and, for non-admins, the
  `features.automations` permission, which is **off** in the code defaults. The calendar needs
  **Calendar** (on) and `features.calendar` (on). Live values are **TO BE CONFIRMED**.
- Schedules are read in the owner's **stored time zone** (reported by the browser at each app
  load), or the **server's local time** when none is stored. Non-admins can be held to a maximum
  number of automations and a minimum interval; both are empty (no limit) in code and have no
  settings screen.
- One background loop runs in **every** server process: due timers every second, due automations
  and calendar reminders every 10 seconds plus up to 2 seconds of jitter. Missed runs are caught up
  **once**. Only PostgreSQL locks rows while claiming; behaviour with several processes on SQLite
  is not established.
- Runs act as the owner, with the owner's model access and **full tool access** (no approval
  pauses). A run is recorded as `success` when the reply **starts**, so a green dot can sit beside a
  chat that ended in an error; the **Runs** list and **View chat** are the evidence.
- The **calendar** gives everyone a `Personal` calendar, adds a read-only **Scheduled Tasks**
  calendar for automations, allows repeats no more often than daily, edits repeating events only
  as whole series, and sends each event's reminder **once**, to its creator only. Sharing,
  attendees and invitation answers exist only in the API.
- **Timers** (set by the model's `timer` tool) are hidden chats that re-prompt their chat when due;
  pending ones survive restarts, but one interrupted while firing is not retried. The tool side is
  in `builtin-native-tools.md`.
- This area matches upstream v0.11.4; the fork only changes notification titles to the site name
  (section 12).

## 1. Purpose and Who Uses It

This area covers three time-based features that share one background scheduler.

| Feature | What it is | Where it lives | Source |
|---|---|---|---|
| **Automation** | A saved prompt that a chosen model runs on a schedule. The schedule is an iCalendar recurrence rule (RRULE). Each run either starts a **new chat** (titled with the automation's name, optionally inside one of the owner's folders) or posts the prompt and the model's reply into a **channel** | `automation` and `automation_run` tables; Automations page | `backend/open_webui/models/automations.py:20-55`, `:63-78`; `backend/open_webui/utils/automations.py:345-518`, `:250-342` |
| **Calendar** | Personal and shared calendars holding events. Events can repeat (no more often than daily), can list attendees who answer an invitation (RSVP), and can raise a reminder ("alert") shortly before they start. Every user gets a calendar named `Personal` automatically. A virtual **Scheduled Tasks** calendar shows the user's automations: upcoming runs and past runs | `calendar`, `calendar_event`, `calendar_event_attendee` tables; Calendar page | `backend/open_webui/models/calendar.py:38-97`, `:266-289`; `backend/open_webui/routers/calendar.py:87-109`, `:195-265` |
| **Timer** | A one-shot reminder that a model sets during a chat with the built-in `timer` tool. When it is due, its prompt is sent back into the same chat and the model answers again | A hidden chat row (in the `chat` table) per timer | `backend/open_webui/utils/timers.py:1`, `:69-168`, `:230-419`; `builtin-native-tools.md` section 5.8 |

The model can also create, change, pause and delete automations, and search, create, change and
delete calendar events, through built-in tools; those tools are documented in
`builtin-native-tools.md` (section 4.3, tools 45 to 53). This document covers the systems behind
them: the pages, the API, the scheduler, the limits, the data and the messages.

### 1.1 Who Uses It

| Who | What they do here | Sections |
|---|---|---|
| Users | Create, edit, pause, resume, run now, clone, import, export and delete their **own** automations; read the run history; keep calendars and events; share calendars; answer invitations; receive reminders | 5, 9 |
| The model (on the user's behalf) | Sets timers; creates and manages automations and calendar events through built-in tools | `builtin-native-tools.md` |
| Admins | Switch **Automations** and **Calendar** on or off for the whole site; grant the `features.automations` and `features.calendar` permissions; allow public calendar sharing; are exempt from the automation count and interval limits | 3, 7 |
| Tier-1 support | Explains schedules, time zones, run history and reminders; checks whether a feature is switched on and permitted; escalates scheduler problems | 11 |

Automations are private to their owner: nobody else, admins included, can open, list or run another
person's automation through the application (section 3.2).

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Pages

| Page | Path | Who sees it | What it shows | Source |
|---|---|---|---|---|
| Automations list | `/automations` | Anyone for whom the site switch is on and who is an admin or holds `features.automations`; everyone else is sent to `/` | Search box **Search Automations**, a status filter (**All**, **Active**, **Paused**), an **Actions** menu (**Enable All**, **Disable All**), header actions **Create**, **Import JSON** and **Export JSON**, and one row per automation with its last run, schedule summary, destination, a menu and an on/off switch; 30 per page | `src/routes/(app)/automations/+layout.svelte:56-63`; `src/routes/(app)/automations/+page.svelte:75-102`, `:359-366`, `:460-737` |
| Automation editor | `/automations/{id}` | As above; an id that is not the user's own returns to `/automations` after an error toast | The full editor (section 5.3) with the run history | `src/routes/(app)/automations/[id]/+page.svelte:18-42`; `src/lib/components/automations/AutomationEditor.svelte` |
| Calendar | `/calendar` | Reachable by anyone who types the path; the page has no client-side check, so when the feature is off or not permitted the server refuses and an error toast appears over an empty calendar | Month, week or day view; **Today**; **Create**; on wide screens a left panel with a small month picker and the list of calendars (hidden on narrow screens) | `src/routes/(app)/calendar/+page.svelte:83-100`, `:201-205`, `:298-372` |

The browser tab title is `Automations / {WEBUI_NAME}` or `Calendar / {WEBUI_NAME}`
(`src/routes/(app)/automations/+page.svelte:411`; `src/routes/(app)/calendar/+page.svelte:212`).

### 2.2 How People Get There

| Entry point | Where | Condition | Source |
|---|---|---|---|
| **Calendar** and **Automations** rows in the user menu (click the name or avatar at the bottom of the sidebar) | User menu | Site switch on and (admin or permission) | `src/lib/components/layout/Sidebar/UserMenu.svelte:333-374`, `:379-421` |
| Pinned sidebar entries **Calendar** and **Automations** | Sidebar | Same condition; not pinned by default (the default pinned items are Notes and Workspace). Holding **Shift** while the user menu is open shows **Pin to Sidebar** / **Unpin from Sidebar** | `src/lib/components/layout/Sidebar.svelte:97`, `:155-206`; `src/lib/components/layout/Sidebar/UserMenu.svelte:55-57`, `:355-372`, `:403-420` |
| A calendar reminder toast | Anywhere in the app | Clicking the toast opens `/calendar` | `src/routes/+layout.svelte:600-628` |
| An automation-run chat | Chat list | Each chat-target run creates a chat titled with the automation's name; it appears in the chat list (or in the chosen folder) | `backend/open_webui/utils/automations.py:398-471` |
| A Scheduled Tasks entry on the calendar | `/calendar` | Clicking a past run opens its chat (`/c/{chat_id}`); clicking an upcoming run, or a past run with no chat, opens `/automations/{automation_id}` | `src/routes/(app)/calendar/+page.svelte:137-150` |

### 2.3 Admin Screens

| Screen | Path | What is here | Source |
|---|---|---|---|
| Admin Settings › General | `/admin/settings/general` | **Calendar** switch ("Allow users to access calendar features.") and **Automations** switch ("Allow users to create and run automations.") | `src/lib/components/admin/Settings/General.svelte:365-378`; `src/lib/i18n/locales/en-US/translation.json:2370-2374` |
| Users › Groups › **Default permissions**, or a group › Permissions | `/admin/users/groups` | Under **Features Permissions**: **Automations** (tooltip `Warning: Enabling this will allow users to run scheduled prompts automatically.`) and **Calendar**. Under **Sharing Permissions**: **Calendars Public Sharing**, shown only while the group's **Calendar** permission is on | `src/lib/components/admin/Users/Groups/Permissions.svelte:235`, `:518-536`, `:960`, `:1114-1151`; `users-groups-roles-and-permissions.md` |
| Workspace › Models › a model › **Builtin Tools** | `/workspace/models` | Per-model **Automations** and **Calendar** tool groups | `builtin-native-tools.md` sections 3.2 and 5.2 |

There is no admin screen that lists users' automations, calendars or timers, and no screen for the
automation count and interval limits (section 7.1).

### 2.4 API Endpoints

Automations are mounted at `/api/v1/automations`; calendars at `/api/v1/calendars` (plural)
(`backend/open_webui/main.py:882-883`). All endpoints need a signed-in `user` or `admin`
(`get_verified_user`) and then the feature checks in section 3.

| Method and path | Purpose | Used by the interface | Source |
|---|---|---|---|
| `GET /api/v1/automations/list` | The user's automations, 30 per page, with `query`, `status` (`active` or `paused`) and `folder_id` filters; each item carries its latest run | Yes | `backend/open_webui/routers/automations.py:162-200` |
| `POST /api/v1/automations/create` | Create | Yes (modal, import) | `:208-238` |
| `GET /api/v1/automations/{id}` | One automation with its latest run and its next five run times | Yes (editor) | `:246-256` |
| `POST /api/v1/automations/{id}/update` | Save changes | Yes | `:264-298` |
| `POST /api/v1/automations/{id}/toggle` | Pause or resume | Yes | `:306-326` |
| `POST /api/v1/automations/{id}/run` | Run now, in the background | Yes | `:334-352` |
| `DELETE /api/v1/automations/{id}/delete` | Delete with its run history | Yes | `:360-380` |
| `GET /api/v1/automations/{id}/runs` | Run history, newest first (`skip`, `limit`, default 50) | Yes (editor) | `:388-400` |
| `GET /api/v1/calendars/` | Calendars the user owns or can read, plus the virtual **Scheduled Tasks** calendar when automations are available to them | Yes | `backend/open_webui/routers/calendar.py:87-109` |
| `POST /api/v1/calendars/create` | Create a calendar (optionally shared) | Yes | `:112-135` |
| `GET /api/v1/calendars/events` | Events between `start` and `end` (ISO 8601), recurring events expanded, plus Scheduled Tasks entries | Yes | `:143-269` |
| `POST /api/v1/calendars/events/create` | Create an event | Yes | `:272-287` |
| `GET /api/v1/calendars/events/search` | Text search over title, description and location (30 per page) | No (the built-in `search_calendar_events` tool reads the database directly, not through this endpoint) | `:290-299` |
| `GET /api/v1/calendars/events/{event_id}` | One event | No | `:302-311` |
| `POST /api/v1/calendars/events/{event_id}/update` | Change an event (including moving it to another calendar) | Yes | `:314-344` |
| `DELETE /api/v1/calendars/events/{event_id}/delete` | Delete an event | Yes | `:347-366` |
| `POST /api/v1/calendars/events/{event_id}/rsvp` | The caller answers an invitation (`accepted`, `declined`, `tentative`, `pending`) | **No** | `:369-388` |
| `GET /api/v1/calendars/{calendar_id}` | One calendar | No | `:396-400` |
| `POST /api/v1/calendars/{calendar_id}/update` | Rename, recolour or change sharing | **No** | `:403-438` |
| `DELETE /api/v1/calendars/{calendar_id}/delete` | Delete a calendar with its events | Yes | `:441-469` |
| `POST /api/v1/calendars/{calendar_id}/default` | Make one of the user's own calendars the default | **No** | `:472-485` |

The interface calls only the functions marked Yes (`src/lib/apis/automations/index.ts`;
`src/lib/apis/calendar/index.ts`; callers in `src/routes/(app)/automations/`,
`src/routes/(app)/calendar/+page.svelte`, `src/lib/components/AutomationModal.svelte`,
`src/lib/components/automations/AutomationEditor.svelte`,
`src/lib/components/calendar/CalendarEventModal.svelte` and
`src/lib/components/calendar/CreateCalendarModal.svelte`). So, in the interface, a person cannot
answer an invitation, rename a calendar, change who it is shared with after creating it, or choose
a different default calendar. There is no endpoint for timers; they are created only by the
`timer` tool (section 5.14).

## 3. Roles and Permissions

### 3.1 Two Gates per Feature

Each feature has a **site switch** (a persistent setting) and a **permission**. The server checks
both on every automation and calendar endpoint; admins skip the permission but **not** the switch.

| Feature | Site switch (key, environment variable, code default) | Permission (code default) | What the server answers when a gate is closed | Source |
|---|---|---|---|---|
| Automations | `automations.enable`, `ENABLE_AUTOMATIONS`, on | `features.automations` (**off**, from `USER_PERMISSIONS_FEATURES_AUTOMATIONS`) | HTTP 403 with the text `401 Unauthorized` | `backend/open_webui/routers/automations.py:45-58`; `backend/open_webui/config.py:1928`, `:2013`, `:2034`, `:3107`; `backend/open_webui/constants.py:69` |
| Calendar | `calendar.enable`, `ENABLE_CALENDAR`, on | `features.calendar` (on, from `USER_PERMISSIONS_FEATURES_CALENDAR`) | HTTP 403 with the text `401 Unauthorized` | `backend/open_webui/routers/calendar.py:37-49`; `backend/open_webui/config.py:1930`, `:2014`, `:2032`, `:3106` |
| Public calendar sharing | none | `sharing.public_calendars` (off, from `USER_PERMISSIONS_CALENDAR_ALLOW_PUBLIC_SHARING`) | No error: a public ("everyone") grant the person may not give is silently dropped when the calendar is saved | `backend/open_webui/routers/calendar.py:116-126`, `:414-426`; `backend/open_webui/config.py:1837-1839`, `:1972` |

With the code defaults, **every non-admin can use the calendar but nobody except admins can use
automations** until an admin turns on `features.automations` in Default permissions or in a group.
The live switch and permission values are data in the `config` table: **TO BE CONFIRMED** for
production (`ground-truth.md`, Settings). Permissions add up across groups and a group cannot take
away a permission the defaults grant (`ground-truth.md`, Accounts and Access).

The interface hides the menu entries when a gate is closed, and the Automations pages send the
person to `/` (section 2.1). The Calendar page has no such check (`src/routes/(app)/calendar/+page.svelte:201-205`).

### 3.2 Automations: Owner Only

| Action | Who may | Notes | Source |
|---|---|---|---|
| List, open, edit, pause, run now, delete, read runs | The owner only | Anyone else, **including an admin**, gets HTTP 404 `We could not find what you're looking for :/` | `backend/open_webui/routers/automations.py:61-66`; `backend/open_webui/constants.py:78` |
| Create more than `automations.max_count` automations | Admins only | Non-admins get HTTP 403 `Automation limit reached ({max_count})` | `backend/open_webui/routers/automations.py:69-83` |
| Schedule more often than `automations.min_interval` seconds | Admins only | Non-admins get HTTP 400 `Schedule too frequent. Minimum interval is {min_interval} seconds.` | `:85-95` |
| Save into a folder | The folder's owner | Another person's folder (or an unknown id) gives HTTP 404 | `:98-106` |
| Post into a channel | Admins; others need `features.channels` and, for a group or direct-message channel, membership, otherwise write access to the channel | Channels switched off or an unknown channel gives HTTP 404; no permission or access gives HTTP 403 `Something went wrong :/` | `:109-144`; `backend/open_webui/constants.py:16-23` |

There is no admin endpoint for other people's automations: the router imports `get_admin_user`
but no route uses it (`backend/open_webui/routers/automations.py:23`), and the only other code that
reads automations is the calendar's Scheduled Tasks view of the person's own automations, folder
deletion and the built-in tools (`backend/open_webui/routers/calendar.py:203`, `:238`;
`backend/open_webui/routers/folders.py:726`; `backend/open_webui/tools/builtin.py:3797-4074`).

### 3.3 What a Run Is Allowed to Do

- **Re-checked at run time.** Before each run the owner is looked up again. If the account is gone
  the run is recorded as failed with `User not found`; if the owner is no longer a `user` or
  `admin`, or (non-admin) no longer holds `features.automations`, it is recorded as failed with
  `Owner no longer permitted to run automations` (`backend/open_webui/utils/automations.py:353-380`).
- **Runs as the owner.** The run uses the owner's account for the whole chat pipeline, so the
  owner's model access, knowledge and tool access apply. For a non-admin, a model they can no
  longer use fails the run with `Model not found` (`backend/open_webui/main.py:1129-1161`;
  `backend/open_webui/utils/models.py:465-520`).
- **Full tool access.** Automation runs and channel replies always use the approval mode `full`:
  no tool call waits for **Allow**/**Deny**, whatever the person's own setting
  (`backend/open_webui/main.py:1254-1264`; `builtin-native-tools.md` sections 3.3 and 5.4).
- **The model's default tools and features.** The run adds the model's default tools, default
  filters and default terminal, and turns on web search or image generation only when the model
  lists it as a default feature, has the capability and the admin switch is on. The code
  interpreter is never turned on for a run (`backend/open_webui/utils/automations.py:166-199`).
- **Run credentials.** A run authenticates to session-based tool servers and terminals as the
  owner for at most `automations.auth_token_expires_in` (default `1h`)
  (`backend/open_webui/utils/automations.py:134-163`, `:384-391`; `backend/open_webui/config.py:2048`).
  How those credentials are formed is security-sensitive: refer to the platform maintainer and
  U of T Information Security (security.utoronto.ca).

### 3.4 Calendars and Events

| Action | Who may | Source |
|---|---|---|
| See a calendar in the list | Its owner, anyone it is shared with (person or group, read or write), everyone when it is shared publicly. Admins see only their own and shared calendars in the list | `backend/open_webui/models/calendar.py:291-317`; `backend/open_webui/models/access_grants.py:723-773` |
| Open a calendar or event by id | Owner, **any admin**, or read access through sharing; otherwise HTTP 403 `Access denied` | `backend/open_webui/routers/calendar.py:62-79`, `:302-311`, `:396-400` |
| Add, change or delete events | Owner, any admin, or **write** access to the calendar; moving an event also needs write access to the destination calendar | `:272-287`, `:314-366` |
| See an event as an attendee | People listed as attendees see the event in their calendar view (unless they declined) even without access to its calendar | `backend/open_webui/models/calendar.py:520-534` |
| Change sharing | Only the owner or an admin (`Only owner can manage sharing`) | `backend/open_webui/routers/calendar.py:410-412` |
| Delete a calendar | Only the owner or an admin (`Only owner can delete calendar`); never the default calendar or Scheduled Tasks | `:441-469` |
| Answer an invitation (RSVP) | The attendee only; organisers cannot set it for others | `:369-388`; `backend/open_webui/models/calendar.py:786-794` |
| Make a calendar the default | Only for one's own calendars | `backend/open_webui/models/calendar.py:372-391` |

### 3.5 Timers

The `timer` tool is offered only with the model's **Sub-agents** tool group, which needs the
`subagents.enable` site switch (code default off); it is refused inside a sub-agent run and for
direct connections (`builtin-native-tools.md` sections 3.2 and 5.8;
`backend/open_webui/tools/builtin.py:1738-1741`; `backend/open_webui/utils/timers.py:100-101`).
When a timer fires, its owner must still be a `user` or `admin`, otherwise it ends with the
internal state `owner no longer permitted to run timers` (`backend/open_webui/utils/timers.py:262-265`).
Timers belong to one person: reading the chat or sending a message cancels only that person's
timers (`backend/open_webui/utils/timers.py:202-227`).

## 4. Key Concepts and Terminology

### 4.1 Glossary

| Term | Meaning | Source |
|---|---|---|
| **Automation** | One saved schedule: a name, a prompt (shown as **Instructions** in the form), a model id, a recurrence rule and a destination, owned by one person. Stored in `automation.data` as `{prompt, model_id, rrule, target, terminal}` | `backend/open_webui/models/automations.py:20-39`, `:73-78` |
| **Run** | One execution of an automation. Each run adds an `automation_run` row with status `success` or `error`, the chat id it produced, and an error text for failures | `backend/open_webui/models/automations.py:42-55`; `backend/open_webui/utils/automations.py:617-625` |
| **Destination** (target) | Where a run writes: **New chat** (a new chat each run), **Folder** (a new chat each run inside one of the owner's folders) or **Channel** (a post plus the model's reply in a channel). Stored as `data.target` (`type` `chat` or `channel`, `channel_id`) and the row's `folder_id` | `src/lib/components/automations/DestinationDropdown.svelte:63-111`; `backend/open_webui/models/automations.py:68-70` |
| **Active / Paused** | The on/off switch (`is_active`). Pausing clears the next run time; resuming computes a fresh one from now, so missed times are not caught up | `backend/open_webui/models/automations.py:264-278` |
| **Next run** | `next_run_at`, the next time the scheduler will run the automation, worked out when the automation is saved, resumed or claimed for a run. The editor shows the first of the next five computed times; **Not scheduled** when there is none (a one-time automation that has already run, or a paused one) | `backend/open_webui/routers/automations.py:147-154`; `src/lib/components/automations/AutomationEditor.svelte:90-95`, `:328-332` |
| **Last run** | `last_run_at`, set when the **scheduler** claims a run, before the run starts. **Run now** does not change it, so after a manual run the list can still say **Never** although the run history shows the run | `backend/open_webui/models/automations.py:334`; `backend/open_webui/routers/automations.py:334-352`; `src/routes/(app)/automations/+page.svelte:226-230` |
| **Recurrence rule (RRULE)** | The iCalendar text that defines the schedule, for example `RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0`. Optional first line `DTSTART:YYYYMMDDTHHMMSS` fixes a start. Parsed by the python-dateutil library | `backend/open_webui/utils/recurrence.py:9`, `:36-83`; `src/lib/components/automations/ScheduleDropdown.svelte:86-105` |
| **One-time (Once)** | A rule `DTSTART:{date}T{time}00` plus `RRULE:FREQ=DAILY;COUNT=1`; after its single run the automation stays switched on but has no next run | `src/lib/components/automations/ScheduleDropdown.svelte:88-91`; `backend/open_webui/utils/recurrence.py:128-139` |
| **Time zone of a schedule** | Rules are read as wall-clock times in the owner's stored time zone (`user.timezone`, which the browser reports on every app load and sign-in). With no stored zone, or an unknown one, the **server's local time** is used. A `Z` or `TZID` in a custom `DTSTART` does not change this | `backend/open_webui/utils/recurrence.py:20-33`, `:128-139`; `src/routes/+layout.svelte:1293-1297`; `src/routes/auth/+page.svelte:59-62`; `ground-truth.md` (Time) |
| **Clock alignment** | Rules that repeat every so many seconds, minutes or hours are aligned to clock boundaries counted from 1 January 2000, so "every 5 minutes" fires at :00, :05, :10 | `backend/open_webui/utils/recurrence.py:37-41`, `:79-83` |
| **Poll** | One pass of the background scheduler: due timers every `TIMER_POLL_INTERVAL` seconds (default 1); due automations and calendar alerts every `SCHEDULER_POLL_INTERVAL` seconds (default 10) plus up to 2 seconds of random jitter | `backend/open_webui/utils/automations.py:53-55`, `:86-126` |
| **Claim** | Taking up to 10 due automations (or 10 due timers) per poll and moving their next run time forward **before** running them, so a run is not repeated by the next poll | `backend/open_webui/models/automations.py:289-340`; `backend/open_webui/utils/timers.py:171-199` |
| **Catch-up run** | When an automation's next run time is already in the past at a poll (the server was down, the site switch was off), it runs **once** and the next time is computed from now; missed occurrences are not replayed one by one | `backend/open_webui/models/automations.py:298-336` |
| **Calendar** | A named, coloured container of events owned by one person. Each person gets one called `Personal` (blue, marked default) the first time their calendar list is empty | `backend/open_webui/models/calendar.py:38-52`, `:266-289` |
| **Default calendar** | The calendar marked `is_default`; it cannot be deleted. The event form pre-selects it | `backend/open_webui/models/calendar.py:372-391`; `backend/open_webui/routers/calendar.py:455-457`; `src/routes/(app)/calendar/+page.svelte:194` |
| **Shared calendar** | A calendar with access grants (people or groups, read or write, or everyone). Sharing is set only through the API; the interface has no sharing control | `backend/open_webui/models/calendar.py:291-317`; section 2.4 |
| **Scheduled Tasks** | A virtual, violet, read-only calendar (id `__scheduled_tasks__`) listing the person's active automations' upcoming runs and their past runs. It is added only when automations are available to the person and cannot be deleted | `backend/open_webui/routers/calendar.py:34`, `:87-109`, `:195-265`, `:445-447` |
| **Event** | One entry with title, optional description and location, start and optional end, all-day flag, optional recurrence, colour and a reminder setting | `backend/open_webui/models/calendar.py:55-79` |
| **Recurring event** | An event with an `rrule`. In the interface: **Daily**, **Monday – Friday**, **Weekly**, **Monthly** or **Yearly**. Any rule that repeats more often than once a day is refused. Occurrences are worked out when the calendar is viewed; they are not stored | `src/lib/components/calendar/CalendarEventModal.svelte:39-45`; `backend/open_webui/models/calendar.py:30`, `:182-193`; `backend/open_webui/utils/calendar.py:17-77` |
| **Reminder (alert)** | A notice shortly before an event starts: **None**, **At time of event**, 5, 10 (default), 15 or 30 minutes, or 1 hour before. Stored as `meta.alert_minutes` (`-1` means none). Once sent, the event is stamped `meta.alerted_at` and is not alerted again | `src/lib/components/calendar/CalendarEventModal.svelte:262-277`; `backend/open_webui/models/calendar.py:716-772`; `backend/open_webui/utils/automations.py:537-614` |
| **Attendee and RSVP** | People invited to an event (`calendar_event_attendee`), each with a status `pending`, `accepted`, `declined` or `tentative`. Attendees and answers are API-only: the interface has no attendee list and no answer buttons | `backend/open_webui/models/calendar.py:82-97`, `:785-842`; `backend/open_webui/routers/calendar.py:369-388` |
| **Timer** | A one-shot reminder for one chat set by the model's `timer` tool, stored as a hidden chat with status `pending`, then `running`, and finally `completed`, `cancelled` or `error` | `backend/open_webui/utils/timers.py:119-157`, `:171-199`, `:202-227`, `:357-361`, `:422-429` |
| **cancel_on** | Events that cancel a pending timer: `chat.read` (the person opens the chat) and `chat.user_message` (the person sends a message in it) | `backend/open_webui/utils/timers.py:91-95`, `:202-227` |

### 4.2 How the Schedule Picker Builds a Rule

The **Schedule** menu in the automation form offers **Once**, **Hourly**, **Daily**, **Weekly**,
**Monthly** and **Custom** (`src/lib/components/automations/ScheduleDropdown.svelte:27-34`). The
example values below are invented.

| Choice | Fields shown | Rule produced (example) | Notes | Source |
|---|---|---|---|---|
| **Once** | Date and time (defaults to about five minutes from now) | `DTSTART:20261103T090000` then `RRULE:FREQ=DAILY;COUNT=1` | The default date is taken from the UTC calendar date, so in the evening west of UTC (after 20:00 EDT or 19:00 EST in Toronto) it defaults to **tomorrow**; check the date before saving | `:53-57`, `:88-91`, `:231-250` |
| **Hourly** | None | `RRULE:FREQ=HOURLY;BYMINUTE=0` | No minute or interval field: it runs at the top of every hour unless an existing rule supplied another minute | `:92-104`, `:229` |
| **Daily** | **Time** | `RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0` | | `:92-104`, `:251-266` |
| **Weekly** | **Time** and day buttons **Mo** to **Su** | `RRULE:FREQ=WEEKLY;BYDAY=MO,WE;BYHOUR=9;BYMINUTE=0` | With no day chosen it repeats on the weekday on which the next run is worked out (normally the day it was saved) | `:36-44`, `:92-104`, `:285-306` |
| **Monthly** | **Time** and **Day** (1 to 31) | `RRULE:FREQ=MONTHLY;BYMONTHDAY=15;BYHOUR=9;BYMINUTE=0` | Days 29 to 31 skip months that do not have them (standard RRULE behaviour) | `:92-104`, `:269-282` |
| **Custom** | Free text, placeholder `RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0` | Exactly what was typed | Starts from the rule of the previously selected choice. Needed for anything else, for example every 15 minutes (`RRULE:FREQ=MINUTELY;INTERVAL=15`) | `:59-64`, `:87`, `:218-228` |

When an existing automation is opened, rules with a frequency other than hourly, daily, weekly or
monthly (and not a one-time rule) open as **Custom** (`:107-141`). The list and the editor show a
plain-English summary such as `Daily at 9:00 AM`, `Every 15 minutes` or `Once · Nov 3 9:00 AM`; the
list's summary is not translated (`src/routes/(app)/automations/+page.svelte:310-349`;
`src/lib/components/automations/AutomationEditor.svelte:97-147`).

Rules without a `DTSTART` line use the moment of evaluation as their start, so daily, weekly and
monthly runs can land up to a minute after the chosen minute (the seconds of that moment), on top
of the poll delay (section 8). This is how python-dateutil fills in missing parts of a rule, read
from the library rather than the repository; see section 14.

### 4.3 What the Calendar Shows

| Item | Shown as | Clicking it | Source |
|---|---|---|---|
| A stored event | A chip with its start time and title in the calendar's colour; month view shows three per day and `+{n} more` | Opens the event form | `src/lib/components/calendar/CalendarEventChip.svelte:12-31`; `src/lib/components/calendar/CalendarView.svelte:184-199` |
| An occurrence of a recurring event | Same, one chip per occurrence | Opens the form for the **whole series** (section 5.11) | `backend/open_webui/utils/calendar.py:59-77` |
| An upcoming automation run | Faded violet chip titled with the automation's name | Opens `/automations/{id}` | `backend/open_webui/routers/calendar.py:202-235`; `src/lib/components/calendar/CalendarEventChip.svelte:15`; `src/routes/(app)/calendar/+page.svelte:139-146` |
| A past automation run | Faded violet chip at the run's time; for failed runs the error text is the description | Opens the run's chat, or the automation when the run has no chat | `backend/open_webui/routers/calendar.py:237-265`; `src/routes/(app)/calendar/+page.svelte:139-146` |

The calendar list on the left (wide screens only) turns each calendar's events on or off for the
current visit; the choice is not saved (`src/routes/(app)/calendar/+page.svelte:83-91`, `:106-114`,
`:348`). Month and day names in the calendar header, the hour labels and `+{n} more` are written in
English in the code and are not translated (`src/routes/(app)/calendar/+page.svelte:39-53`;
`src/lib/components/calendar/CalendarView.svelte:114-119`, `:197`).

## 5. Workflows (Step by Step)

### 5.1 Switch the Features On (Admins)

1. **Admin Settings › General** (`/admin/settings/general`): turn on **Calendar** and/or
   **Automations** and save. Both are on in the code defaults (`backend/open_webui/config.py:2032-2034`).
   The save goes to `POST /api/v1/auths/admin/config` and is stored at once in the `config` table
   (`backend/open_webui/routers/auths.py:104-133`, `:1270-1296`).
2. **Users › Groups** (`/admin/users/groups`): in **Default permissions** or a group's permissions,
   under **Features Permissions**, turn on **Automations** (off by default) and/or **Calendar** (on by
   default). The Automations switch carries the tooltip
   `Warning: Enabling this will allow users to run scheduled prompts automatically.`
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:1114-1151`).
3. People see the **Automations** and **Calendar** rows in their user menu after the app reloads its
   configuration (the switches arrive through `/api/config` as `enable_automations` and
   `enable_calendar`, `backend/open_webui/main.py:2357-2358`).

There is no screen for the count and interval limits; see section 7.1.

### 5.2 Create an Automation

1. Open **Automations** (user menu, or `/automations`) and choose **Create** in the header
   (`src/routes/(app)/automations/+page.svelte:75-102`).
2. In the form (`src/lib/components/AutomationModal.svelte:150-224`):
   - type a name in **Automation title**;
   - write the prompt under **Instructions** (placeholder `Enter prompt here.`). Template variables
     such as `{{CURRENT_DATE}}`, `{{CURRENT_TIME}}`, `{{CURRENT_WEEKDAY}}` and `{{USER_NAME}}` are
     filled in at run time; the date and time come from the **server's** clock, not the person's
     time zone (`backend/open_webui/utils/task.py:36-104`; `backend/open_webui/utils/automations.py:382`);
   - pick the schedule (section 4.2);
   - pick a model (**Select model**; the list shows the models the person can use, without hidden
     ones) (`src/lib/components/automations/ModelDropdown.svelte:23-35`);
   - pick the destination: **New chat**, a **Folder** (the person's own folders only, not shared
     ones) or a **Channel** (any channel in their list except direct messages)
     (`src/lib/components/automations/DestinationDropdown.svelte:37-43`, `:143-207`).
3. Choose **Create**. The browser checks first: `Name, prompt, and model are required`,
   `Channel is required`, and for **Once** `Scheduled time must be in the future` (judged by the
   browser's clock) (`src/lib/components/AutomationModal.svelte:45-60`).
4. The server then checks, in order: the feature gates; the folder; the channel; the rule (valid,
   has a future run, `COUNT` only with `DTSTART`, evaluates within 2 seconds); for non-admins the
   count limit and the minimum interval (`backend/open_webui/routers/automations.py:208-226`;
   `backend/open_webui/utils/recurrence.py:106-125`). Messages are listed in section 10.
5. On success the toast `Automation created` appears and the editor page for the new automation
   opens (`src/lib/components/AutomationModal.svelte:81-84`;
   `src/routes/(app)/automations/+page.svelte:448-458`). New automations are active at once; the
   first run is the next occurrence of the rule after now, in the person's time zone
   (`backend/open_webui/routers/automations.py:228-229`).

### 5.3 Open and Edit an Automation

1. Click an automation's row, or choose **Edit** in its **More** menu; both open `/automations/{id}`
   (`src/routes/(app)/automations/+page.svelte:590-605`, `:665-669`).
2. The page shows **Status** (**Active** or **Paused**), **Schedule** (a summary), **Destination**
   (**New chat**, `Folder: {name}` or `#{channel}`), **Model** (the model id), **Next run**,
   **Last run**, the **Prompt** and **Runs** (section 5.8)
   (`src/lib/components/automations/AutomationEditor.svelte:281-416`). Times are shown in the
   browser's own time zone.
3. The header has the on/off switch, **Run now**, **Edit** and **Delete**
   (`src/lib/components/automations/AutomationItemHeaderActions.svelte:22-70`).
4. **Edit** opens the same form as creation with the saved values; **Save** sends everything again
   and shows `Automation updated` (`src/lib/components/AutomationModal.svelte:75-79`). The server
   repeats the checks of 5.2 except the count limit, and recomputes the next run from now
   (`backend/open_webui/routers/automations.py:264-298`). Saving does not run the automation.
5. Saving a paused automation keeps it paused but still stores a next run time; it does not run
   while paused because the scheduler only takes active rows
   (`backend/open_webui/models/automations.py:225-245`, `:298-303`).

### 5.4 Pause, Resume, Enable All and Disable All

- The switch on each row, or in the editor header, pauses or resumes one automation through
  `POST /api/v1/automations/{id}/toggle` (`src/routes/(app)/automations/+page.svelte:165-173`, `:699-717`;
  `src/lib/components/automations/AutomationEditor.svelte:149-161`).
- Pausing clears the next run; resuming computes the next occurrence after now. Runs missed while
  paused are not made up (`backend/open_webui/models/automations.py:264-278`).
- **Actions › Enable All** or **Disable All** switches every automation that matches the current
  search and status filter, across all pages, with no confirmation
  (`src/routes/(app)/automations/+page.svelte:175-193`, `:535-566`).

### 5.5 Run Now

1. Choose **Run Now** in a row's **More** menu, or **Run now** (play button) in the editor header.
2. The server starts the run in the background on the process that received the click and answers
   at once; the toast `Automation triggered` means the run was **started**, not that it finished
   (`backend/open_webui/routers/automations.py:334-352`;
   `src/routes/(app)/automations/+page.svelte:195-203`).
3. The editor reloads the run list two seconds later
   (`src/lib/components/automations/AutomationEditor.svelte:163-174`).
4. **Run now** works on paused automations too, does not change the next scheduled run and does not
   update **Last run** (`backend/open_webui/routers/automations.py:341-352`). Pressing it again
   starts another run.

### 5.6 Clone, Import and Export

- **Clone** (row menu) opens the create form filled with the same values, the name
  `{name} (Clone)`, switched on; the folder and channel are kept only if they are still in the
  person's lists (`src/routes/(app)/automations/+page.svelte:218-224`;
  `src/lib/components/AutomationModal.svelte:117-133`).
- **Export JSON** downloads every automation the person owns as `automations-export-{timestamp}.json`
  with name, folder, data (prompt, model, rule, destination) and on/off state
  (`src/routes/(app)/automations/+page.svelte:260-280`). The file contains the prompts; treat it as
  the person's data.
- **Import JSON** reads such a file (a list, or an object with an `automations` list) and creates
  the automations one at a time with the normal checks. A folder id that is not one of the
  importer's folders is dropped. The first failure stops the import with an error toast, leaving
  the ones already created; importing the same file twice creates duplicates. On success:
  `Imported automations successfully` (`src/routes/(app)/automations/+page.svelte:282-308`, `:426-446`).

### 5.7 Delete an Automation

1. Row **More › Delete**, or **Delete** in the editor header, opens the dialog
   **Delete automation?** with `This will delete {name}.` and **Cancel** / **Confirm**
   (`src/routes/(app)/automations/+page.svelte:414-424`;
   `src/lib/components/automations/AutomationEditor.svelte:269-277`;
   `src/lib/components/common/ConfirmDialog.svelte:21-22`).
2. **Holding Shift** over the list replaces each row's menu with a bin button that deletes
   **immediately, without the dialog** (`src/routes/(app)/automations/+page.svelte:372-376`, `:648-662`).
3. The server deletes the automation's whole run history and then the automation; the toast reads
   `Deleted {name}` (`backend/open_webui/routers/automations.py:360-380`;
   `src/routes/(app)/automations/+page.svelte:205-216`). The chats that earlier runs created are
   **kept**; deletion is permanent and there is no undo in the code.

### 5.8 Tell Whether a Run Happened or Failed

| Where | What it tells you | Source |
|---|---|---|
| The automation's **Runs** list (editor page) | One line per run, newest first, 50 at a time with more on scroll: a green dot for `success` or a red dot for `error`, the time, **View chat** or **View channel** when the run produced one, and the error text in red. **No runs yet** when there are none | `src/lib/components/automations/AutomationEditor.svelte:200-236`, `:358-415` |
| **Last run** in the list and editor | When the scheduler last claimed it (not manual runs) | section 4.1 |
| **Next run** | The next scheduled time, or **Not scheduled** | section 4.1 |
| The chat list | A chat named after the automation for each chat or folder run | `backend/open_webui/utils/automations.py:407-446` |
| The calendar's **Scheduled Tasks** | Past runs at their times; failed runs carry the error as the description | `backend/open_webui/routers/calendar.py:237-265` |

**What `success` means.** A run is recorded as `success` when the model reply has been **started**,
because the chat pipeline answers as soon as it has queued the reply. If the model then fails (for
example the provider refuses or times out), the error appears on the reply inside the chat while the
run list still shows a green dot (`backend/open_webui/utils/automations.py:494-511`;
`backend/open_webui/main.py:1802-1881`, `:1686-1712`). Always open the chat to confirm the answer.

**What `error` means.** The run stopped before the reply started. The recorded text is the reason,
for example `User not found`, `Owner no longer permitted to run automations`,
`Failed to create chat`, `Channel not found`, or an error passed up from the chat pipeline, which
is written with its HTTP status in front, such as `400: Model not found` (an HTTP error's text is
`{status}: {detail}` in the installed Starlette library, `.venv/lib/python3.12/site-packages/starlette/exceptions.py:15-16`)
(`backend/open_webui/utils/automations.py:353-380`, `:448-458`, `:258-261`, `:520-529`;
`backend/open_webui/main.py:1638-1645`). Error texts are cut to 4,000 characters.

**When there is no record at all**, the run never started: the site switch was off, the server was
down (it will catch up once, section 8), the rule could not be evaluated in time (the server log
says `Skipping automation {id}: recurrence evaluation timed out` and the automation is retried at
every poll), or the process stopped between claiming and recording the run
(`backend/open_webui/utils/automations.py:104-114`; `backend/open_webui/models/automations.py:328-333`).

### 5.9 What a Scheduled Run Does (New Chat or Folder)

1. **Claim** (every poll, up to 10 due automations, oldest first): for each, the next run time is
   recomputed from now in the owner's time zone and **Last run** is set to now; both are saved
   before anything runs (`backend/open_webui/models/automations.py:289-340`).
2. **Owner check** (section 3.3).
3. **Prompt**: template variables are filled in (`backend/open_webui/utils/automations.py:382`).
4. **Folder check**: if the saved folder no longer exists, the automation's folder is cleared and
   the chat is created outside any folder (`:398-401`).
5. **Chat**: a new chat is created for the owner, titled with the automation's name, holding the
   prompt as the first message and an empty reply; the browser is told to refresh its chat list
   (`:403-471`). No title, tag or follow-up generation is requested (`:490`).
6. **Reply**: the same pipeline as the chat page runs with the owner's account, the model's
   defaults (section 3.3) and full tool access; the reply streams into the new chat
   (`:473-495`; `chat-completion-pipeline-and-generation-tasks.md`).
7. **Record**: an `automation_run` row (`success` with the chat id, or `error`) and an application
   event (`automation.run_completed` or `automation.run_failed`) (`:497-529`; section 9).

If the person has the app open on another page, the normal background-reply toast appears when the
reply finishes, titled with the automation's name, and a browser notification if they enabled
**Browser Notifications** (`src/routes/+layout.svelte:735-781`). The server also sends an
`automation:result` message to the person's browser sessions, but no part of the interface listens
for it (`backend/open_webui/utils/automations.py:497-509`; no listener in `src/`).

### 5.10 What a Channel Run Does

1. The channel must still exist and the **Channels** site switch must be on, otherwise the run
   fails with `Channel not found` (`backend/open_webui/utils/automations.py:258-261`).
2. The prompt is posted in the channel **as the owner**, then an empty reply from the model is
   added: in a thread under the post when the channel response mode is `thread` (the code default),
   otherwise directly in the channel (`:263-300`; `backend/open_webui/config.py:2030`).
3. The model is told it is participating in a channel conversation and to be concise and
   conversational, and receives the prompt prefixed with the owner's name (`:302-319`).
4. The posting rules of channels apply to the owner (membership for group and direct-message
   channels, write access otherwise); a refusal is recorded as the run's error
   (`backend/open_webui/routers/channels.py:1137-1160`; `channels-and-direct-messages.md`).
5. The run is recorded with the chat id `channel:{id}`; **View channel** opens `/channels/{id}`
   (`:335`; `src/lib/components/automations/AutomationEditor.svelte:379-397`).

### 5.11 Create, Edit and Delete Calendar Events

**Create.**

1. On `/calendar`, choose **Create** (top right), click a day in month view (pre-fills 09:00 to
   10:00 that day) or click an hour in week or day view (pre-fills that hour)
   (`src/routes/(app)/calendar/+page.svelte:131-135`, `:172-176`, `:335-340`;
   `src/lib/components/calendar/CalendarView.svelte:121-138`).
2. Fill in the form (`src/lib/components/calendar/CalendarEventModal.svelte:198-305`): **Event title**;
   **Calendar** (every calendar in the person's list except Scheduled Tasks, the default one
   pre-selected); **When** (a date, a start and an end time, or **All day**); **Location**;
   **Reminder** (default **10 minutes before**); **Repeat** (default **No Repeat**); **Description**.
3. Choose **Create**. The browser requires a title (`Title is required`) and a date
   (`Date is required`) (`:118-127`).
4. Dates and times are read in the **browser's** time zone. **All day** stores 00:00 to 23:59 of the
   chosen day. If the end is before the start, the end is set equal to the start
   (`:60-76`, `:131-137`).
5. The server needs write access to the chosen calendar and checks the recurrence (no more often
   than daily, valid, evaluated within 2 seconds); the toast `Event created` confirms
   (`backend/open_webui/routers/calendar.py:272-287`; `backend/open_webui/models/calendar.py:182-193`, `:447-478`).

The form has no attendee field and no end-date field: the end date stays at the date the form
opened with, so moving the start to another day can stretch or shorten the event (behaviour read
from the code, `:28-31`, `:95-108`, `:224-250`; see section 14).

**Edit.** Click the event, change it and choose **Save** (`Event updated`) (`:139-155`). The
reminder setting is merged into the event's stored settings, so a reminder that has already been
sent is **not** sent again after the event is moved (section 5.13).

**Recurring events.** **Repeat** offers **Daily** (`FREQ=DAILY`), **Monday – Friday**
(`FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR`), **Weekly** (`FREQ=WEEKLY`), **Monthly** (`FREQ=MONTHLY`) and
**Yearly** (`FREQ=YEARLY`); each repeats from the event's own start (`:39-58`, `:279-293`;
`backend/open_webui/utils/calendar.py:47-51`). Three things to know:

- Clicking any occurrence opens the **whole series**, with that occurrence's date and time in the
  form. Saving moves the series to start at that occurrence, so earlier occurrences disappear;
  **Delete** removes the whole series. There is no "this occurrence only" option
  (`src/routes/(app)/calendar/+page.svelte:137-150`;
  `src/lib/components/calendar/CalendarEventModal.svelte:78-90`, `:139-150`, `:182-195`;
  `backend/open_webui/utils/calendar.py:59-77`).
- A recurrence the form does not recognise (one set through the API) shows as **No Repeat**, and
  saving the form **removes** it (`src/lib/components/calendar/CalendarEventModal.svelte:51-58`, `:147`).
- Any rule that repeats more often than daily is refused with
  `Recurring events cannot repeat more often than daily` (`backend/open_webui/models/calendar.py:30`,
  `:182-193`; `backend/open_webui/constants.py:123`).

**Delete.** **Delete** in the form opens **Delete Event** with
`This action cannot be undone. Do you wish to continue?`; confirming deletes the event and its
attendee rows and shows `Event deleted` (`src/lib/components/calendar/CalendarEventModal.svelte:182-195`,
`:347-351`; `backend/open_webui/models/calendar.py:774-782`). Scheduled Tasks entries cannot be
edited or deleted from the calendar; clicking them navigates instead (section 4.3).

### 5.12 Calendars: Create, Show or Hide, Delete

1. **Create**: in the left panel (wide screens), the **New calendar** button opens **New Calendar**
   with **Name** (placeholder `Calendar name`) and **Color** (eight presets or **Custom color**).
   **Create** shows `Calendar created`; an empty name shows `Name is required`
   (`src/lib/components/calendar/CalendarSidebar.svelte:184-200`;
   `src/lib/components/calendar/CreateCalendarModal.svelte:39-148`). New calendars are private
   (no sharing) and not the default (`backend/open_webui/models/calendar.py:325-345`).
2. **Show or hide**: click a calendar's name to hide or show its events for this visit
   (`src/lib/components/calendar/CalendarSidebar.svelte:203-213`).
3. **Delete**: hover a calendar that is neither the default nor Scheduled Tasks and choose the bin
   (**Delete calendar**). The dialog **Delete Calendar** says
   `This will permanently delete the calendar "{{name}}" and all its events. This action cannot be undone.`
   Confirming shows `Calendar deleted`, or `Failed to delete calendar`, or the server's refusal
   (`src/lib/components/calendar/CalendarSidebar.svelte:19-34`, `:94-103`, `:225-245`;
   `src/routes/(app)/calendar/+page.svelte:116-129`). The bin also appears on calendars shared with
   the person; deleting one of those is refused (section 3.4).
4. **Not available in the interface**: renaming or recolouring a calendar, sharing it or changing
   its sharing, choosing another default, inviting attendees and answering invitations
   (section 2.4).

The person's first calendar, `Personal`, is created automatically the first time their calendar
list would otherwise be empty. If a calendar shared with everyone already shows in their list, no
`Personal` calendar is created and the shared calendar may be pre-selected in the event form
(`backend/open_webui/models/calendar.py:291-312`; `src/routes/(app)/calendar/+page.svelte:194`;
behaviour read from code, see section 14).

### 5.13 Reminders (Calendar Alerts)

1. Every `SCHEDULER_POLL_INTERVAL` seconds, while `calendar.enable` is on, the scheduler looks for
   events that are not cancelled and start between about 15 seconds ago (poll interval plus 5
   seconds) and 60 minutes from now (`backend/open_webui/utils/automations.py:116-121`, `:537-553`;
   `backend/open_webui/models/calendar.py:716-751`).
2. An event qualifies when its start is within its reminder setting (`meta.alert_minutes`; without
   one, `CALENDAR_ALERT_LOOKAHEAD_MINUTES`, code default 10). `-1` means no reminder. Because the
   search window is 60 minutes, a reminder set further ahead through the API is sent about an hour
   before (`backend/open_webui/models/calendar.py:736-772`).
3. Events already stamped `meta.alerted_at` are skipped. Otherwise the scheduler:
   - sends `calendar:alert` to the **event's creator's** open browser sessions (not to attendees or
     to people the calendar is shared with);
   - stamps the event `alerted_at`;
   - publishes the application event `calendar.alert`, which also reaches the creator's personal
     notification targets (section 9)
   (`backend/open_webui/utils/automations.py:558-614`).
4. In the browser: a toast with the event title and `Starting now`, `Starting in 1 minute` or
   `Starting in {{count}} minutes`, shown for 30 seconds; clicking it opens `/calendar`. In the
   most recently active tab, a browser notification `{title} / {WEBUI_NAME}` too, when the person
   has switched on **Browser Notifications** (`src/routes/+layout.svelte:600-628`;
   `src/lib/components/chat/Settings/Notifications.svelte:59-77`).

Consequences, all read from the code:

- Each event is alerted **once**. A recurring event alerts only for its first start (the stored
  start), not for later occurrences (`backend/open_webui/models/calendar.py:741-750`).
- Moving or editing an event after its reminder has gone out does not re-arm it, because the
  stamp is kept (`backend/open_webui/models/calendar.py:704-707`).
- An all-day event's reminder is counted from 00:00 of that day (section 5.11).
- If the server is down when a reminder is due, it is sent at the next poll as long as the event
  has not started more than about 15 seconds earlier; otherwise it is skipped.

### 5.14 Timers

The model sets a timer with the `timer` tool; the full tool-side workflow (relative or absolute
time, `cancel_on`, how the fired prompt appears as a collapsed **Timer** row in the chat) is in
`builtin-native-tools.md` section 5.8. The scheduling side:

1. The timer is stored as a hidden chat with status `pending` and a due time (`chat.timer_at`, in
   nanoseconds) (`backend/open_webui/utils/timers.py:119-157`; `backend/open_webui/models/chats.py:153`).
2. Every `TIMER_POLL_INTERVAL` seconds (default 1) every server process claims up to 10 due timers,
   marking each `running` and clearing its due time (`backend/open_webui/utils/automations.py:89-96`;
   `backend/open_webui/utils/timers.py:171-199`).
3. If the parent chat is busy with a reply, the timer goes back to `pending` with its original due
   time and is tried again at the next poll (`backend/open_webui/utils/timers.py:295-308`).
4. Otherwise the prompt is added to the parent chat after the latest finished reply, a reply is
   started with the settings captured when the timer was set, the timer becomes `completed` and the
   browser is told to reload the chat (`:310-416`).
5. Opening the chat (`chat.read`) or sending a message in it (`chat.user_message`) cancels the
   person's pending timers on that chat that asked for it (`:202-227`;
   `backend/open_webui/socket/main.py:634-638`; `backend/open_webui/main.py:1539-1547`).
6. Deleting the parent chat deletes its timers (`backend/open_webui/routers/chats.py:1598-1601`).

**After a restart.** Pending timers are kept in the database, and any that fell due while the server
was down fire at the first poll. A timer that had been claimed but not finished when the process
stopped stays `running` and is not retried: no code resets it (`backend/open_webui/utils/timers.py:171-199`,
`:230-244`; no other reference to the `running` state in `backend/open_webui`).

## 6. Data Model

All times in the automation and calendar tables are **nanoseconds** since 1 January 1970 (UTC)
(`time.time_ns()`); divide by 1,000,000,000 for seconds (`ground-truth.md`, Time). No column has a
database foreign key; the links below are by id only. The tables are created by the migrations
`d4e5f6a7b8c9` (automations), `959eaac8f909` (automation folder) and `56359461a091` (calendars),
and the timer column by the head migration `d4c1a8e37b62`
(`backend/open_webui/migrations/versions/d4e5f6a7b8c9_add_automation_tables.py:25-70`;
`backend/open_webui/migrations/versions/959eaac8f909_add_automation_folder_id.py:21-36`;
`backend/open_webui/migrations/versions/56359461a091_add_calendar_tables.py`;
`backend/open_webui/migrations/versions/d4c1a8e37b62_add_chat_timer_at_and_chat_indexes.py:22-54`).

### 6.1 `automation`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | Random UUID | `backend/open_webui/models/automations.py:23`, `:143` |
| `user_id` | text | Owner | `:24` |
| `folder_id` | text, nullable | Folder for chat runs; cleared when the folder is deleted or found missing at run time | `:25`; `backend/open_webui/routers/folders.py:726`; `backend/open_webui/utils/automations.py:398-401` |
| `name` | text | Name; also the title of each run's chat | `:26` |
| `data` | JSON | `prompt`, `model_id`, `rrule`, `target` (`type` `chat` or `channel`, `channel_id`) and `terminal` (`server_id`, `cwd`) | `:27`, `:63-78` |
| `meta` | JSON, nullable | Free-form; the interface only passes it through | `:28` |
| `is_active` | boolean | On (active) or paused | `:29` |
| `last_run_at` | big integer, nullable | Time of the last **scheduled** claim | `:30`, `:334` |
| `next_run_at` | big integer, nullable | Next due time; empty when paused or when the rule has no more occurrences | `:31`, `:275`, `:335` |
| `created_at`, `updated_at` | big integer | Nanoseconds | `:33-34` |

Indexes: `ix_automation_next_run` (`next_run_at`) and `ix_automation_user_folder` (`user_id`,
`folder_id`) (`:36-39`). `data.terminal` is accepted and stored, but no code in v0.11.4 reads it
when a run executes: the helper that would set a terminal's working directory is never called,
and the terminal pickers in `src/lib/components/automations/TerminalDropdown.svelte` and
`FolderDropdown.svelte` are not used by any page (`backend/open_webui/utils/automations.py:202-247`;
no caller in `backend/open_webui` or `src/`). A run uses the model's own default terminal instead
(`:166-176`).

### 6.2 `automation_run`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | Random UUID | `backend/open_webui/models/automations.py:45` |
| `automation_id` | text | The automation | `:46` |
| `chat_id` | text, nullable | The chat created, or `channel:{channel id}` for channel runs; empty for failures | `:47`; `backend/open_webui/utils/automations.py:335`, `:511` |
| `status` | text | `success` or `error` (section 5.8 explains what `success` covers) | `:48` |
| `error` | text, nullable | Failure reason, at most 4,000 characters | `:49`; `backend/open_webui/utils/automations.py:522` |
| `created_at` | big integer | When the run was recorded (nanoseconds) | `:50`, `:364` |

The model declares indexes `ix_automation_run_automation_id` and `ix_automation_run_aid_created`
(`:52-55`); only the first is created by a migration, so databases built by migrations lack the
second (it affects only query speed). Run rows are removed only when their automation is deleted
(`:426-430`); nothing else trims the history.

### 6.3 `calendar`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | Random UUID | `backend/open_webui/models/calendar.py:41` |
| `user_id` | text | Owner | `:42` |
| `name`, `color` | text | Name and colour (`#3b82f6` for `Personal`) | `:43-44`, `:281-282` |
| `is_default` | boolean | The owner's default calendar; set only for `Personal` or through the default endpoint | `:45`, `:283`, `:372-391` |
| `data`, `meta` | JSON, nullable | Free-form; merged on update | `:46-47`, `:361-364` |
| `created_at`, `updated_at` | big integer | Nanoseconds | `:49-50` |

Sharing is not a column: it is stored as rows in the `access_grant` table with resource type
`calendar` (`:251-252`, `:343-344`, `:365-366`; `users-groups-roles-and-permissions.md`). The
Scheduled Tasks calendar is not stored; the list adds it on the fly with `is_system` true
(`backend/open_webui/routers/calendar.py:94-107`).

### 6.4 `calendar_event`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | Random UUID | `backend/open_webui/models/calendar.py:58` |
| `calendar_id` | text | Calendar it belongs to | `:59` |
| `user_id` | text | **Creator** (receives the reminder) | `:60`; `backend/open_webui/utils/automations.py:584` |
| `title`, `description`, `location` | text | Shown in the form and the toast | `:61-62`, `:68` |
| `start_at`, `end_at` | big integer | Start and optional end (nanoseconds); for a recurring event, the first occurrence | `:63-64` |
| `all_day` | boolean | All-day flag | `:65` |
| `rrule` | text, nullable | Recurrence (no more often than daily) | `:66`, `:182-193` |
| `color` | text, nullable | Per-event colour (the interface does not set it) | `:67` |
| `data` | JSON, nullable | Free-form | `:69` |
| `meta` | JSON, nullable | `alert_minutes` (reminder), `alerted_at` (when the reminder was sent) | `:70`, `:757-767`; `backend/open_webui/utils/automations.py:588-592` |
| `is_cancelled` | boolean | Cancelled events are hidden from views and searches and get no reminder; only the API and the model's `update_calendar_event` tool can set it | `:71`, `:544`, `:624`, `:746` |
| `created_at`, `updated_at` | big integer | Nanoseconds | `:73-74` |

Indexes `ix_calendar_event_calendar` (`calendar_id`, `start_at`) and `ix_calendar_event_user_date`
(`user_id`, `start_at`) (`:76-79`). Occurrences of recurring events are computed on request (up to
5,000 per event per view) and never stored (`backend/open_webui/utils/calendar.py:17-77`).

### 6.5 `calendar_event_attendee`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | Random UUID | `backend/open_webui/models/calendar.py:85` |
| `event_id`, `user_id` | text | Event and invited person; one row per pair (`uq_event_attendee`) | `:86-87`, `:94-95` |
| `status` | text | `pending` (new), `accepted`, `declined`, `tentative`; kept when the organiser re-saves the list | `:88`, `:786-823` |
| `meta` | JSON, nullable | Free-form | `:89` |
| `created_at`, `updated_at` | big integer | Nanoseconds | `:91-92` |

### 6.6 Timers in the `chat` Table

A timer is a row in `chat` (`chat-conversations-history-and-organisation.md`) whose `meta` marks it
internal; the chat list and chat search queries leave such rows out
(`backend/open_webui/models/chats.py:182-183`, `:1488-1501`, `:1963-2019`).

| Field | Meaning | Source |
|---|---|---|
| `chat.timer_at` | Due time in nanoseconds; set only while the timer is `pending` | `backend/open_webui/models/chats.py:153` |
| `meta.internal`, `meta.type` | `true` and `timer` | `backend/open_webui/utils/timers.py:144-146` |
| `meta.parent_chat_id`, `meta.parent_message_id` | The chat the timer belongs to | `:147-148` |
| `meta.status` | `pending`, `running`, `completed`, `cancelled` or `error` | `:150`, `:191`, `:221`, `:359`, `:422-429` |
| `meta.timer_at`, `meta.timer_started_at`, `meta.timer_completed_at`, `meta.timer_cancelled_at` | Times in nanoseconds | `:149`, `:192`, `:222`, `:360` |
| `meta.timer_cancelled_by` | `chat.read` or `chat.user_message` | `:223` |
| `meta.timer_error` | Failure reason (at most 500 characters for reply failures) | `:248-270`, `:419` |
| `meta.cancel_on`, `meta.run` | Cancel events and the captured model, tools, skills, filters, features, files and variables | `:106-117`, `:153-154` |

The hidden chat's own `created_at` and `updated_at` are in **seconds** like every chat
(`backend/open_webui/models/chats.py:558-560`; `backend/open_webui/utils/timers.py:196`).

### 6.7 What Deleting Removes

| Action | Removed | Kept | Source |
|---|---|---|---|
| Delete an automation | The automation and all its run rows | Every chat and channel post its runs created | `backend/open_webui/routers/automations.py:370-371` |
| Delete a folder | Nothing in this area | Automations that used it, now saving to no folder | `backend/open_webui/routers/folders.py:726` |
| Delete a chat | Its hidden timer chats | Run rows that point to it (**View chat** then leads nowhere) | `backend/open_webui/routers/chats.py:1598-1601` |
| Delete a calendar (not the default) | The calendar, its events, their attendee rows, its sharing grants | Nothing | `backend/open_webui/models/calendar.py:393-423` |
| Delete an event | The event and its attendee rows | Nothing | `backend/open_webui/models/calendar.py:774-782` |
| Delete a user | Not automations, runs, calendars, events or attendee rows (`ground-truth.md`, Accounts) | All of them. The scheduler keeps claiming a deleted owner's active automations and records `User not found` at every scheduled time | `backend/open_webui/models/automations.py:298-303`; `backend/open_webui/utils/automations.py:353-362` |
| Switch Automations or Calendar off | Nothing | All data; runs simply stop being claimed and reminders stop being sent | `backend/open_webui/utils/automations.py:104-121` |

## 7. Settings and Configuration

The live value of every setting below is data (the `config` table or the environment) and is
**TO BE CONFIRMED** for production; the defaults are what the code says. After first boot a stored
value wins over its environment variable (`ground-truth.md`, Settings).

### 7.1 Persistent Settings

| Key | Environment variable (first boot) | Code default | Where an admin changes it | Effect | Source |
|---|---|---|---|---|---|
| `automations.enable` | `ENABLE_AUTOMATIONS` | on | Admin Settings › General › **Automations** | Gates the Automations pages and API for everyone, and whether the scheduler claims due automations at all | `backend/open_webui/config.py:2034`, `:3107`; `backend/open_webui/routers/automations.py:45-51`; `backend/open_webui/utils/automations.py:104-105` |
| `calendar.enable` | `ENABLE_CALENDAR` | on | Admin Settings › General › **Calendar** | Gates the calendar API for everyone and whether reminders are sent | `backend/open_webui/config.py:2032`, `:3106`; `backend/open_webui/routers/calendar.py:37-44`; `backend/open_webui/utils/automations.py:116-117` |
| `automations.max_count` | `AUTOMATION_MAX_COUNT` | empty (no limit) | **No screen**; only the admin configuration API (field `AUTOMATION_MAX_COUNT`) or the environment at first boot | Most automations a non-admin may own, paused ones included; checked only when creating | `backend/open_webui/config.py:2044`, `:3115`; `backend/open_webui/routers/auths.py:122`, `:1227`, `:1278`; `backend/open_webui/routers/automations.py:74-83`; `backend/open_webui/models/automations.py:158-161` |
| `automations.min_interval` | `AUTOMATION_MIN_INTERVAL` | empty (no limit) | As above (field `AUTOMATION_MIN_INTERVAL`) | Shortest allowed gap, in seconds, between the next two runs of a non-admin's rule, on create and update. A one-time rule has no second run and is not limited | `backend/open_webui/config.py:2046`, `:3116`; `backend/open_webui/routers/auths.py:123`, `:1228`, `:1279-1281`; `backend/open_webui/routers/automations.py:85-95`; `backend/open_webui/utils/recurrence.py:160-171` |
| `automations.auth_token_expires_in` | `AUTOMATION_AUTH_TOKEN_EXPIRES_IN` | `1h` | Not editable on any screen or through the admin configuration API | How long a run may act as its owner towards tool servers and terminals; an unreadable value falls back to one hour. Security-sensitive detail: refer to the platform maintainer and U of T Information Security | `backend/open_webui/config.py:2048`, `:3117`; `backend/open_webui/utils/automations.py:384-391` |
| `user.permissions` › `features.automations` | `USER_PERMISSIONS_FEATURES_AUTOMATIONS` | off | Users › Groups › Default permissions or a group › **Automations** | Who may use automations (admins always may) | `backend/open_webui/config.py:1928`, `:2013` |
| `user.permissions` › `features.calendar` | `USER_PERMISSIONS_FEATURES_CALENDAR` | on | Same place › **Calendar** | Who may use the calendar | `backend/open_webui/config.py:1930`, `:2014` |
| `user.permissions` › `sharing.public_calendars` | `USER_PERMISSIONS_CALENDAR_ALLOW_PUBLIC_SHARING` | off | Same place › Sharing Permissions › **Calendars Public Sharing** | Whether a non-admin may share a calendar with everyone (API only) | `backend/open_webui/config.py:1837-1839`, `:1972`; `backend/open_webui/routers/calendar.py:116-126`, `:414-426` |

With the code defaults there is **no** minimum interval: a non-admin can use a custom rule that
repeats every second, and the only brake is the scheduler's poll interval (section 8). Setting
`automations.min_interval` is the admin's protection against very frequent runs.

Other settings that change behaviour in this area:

| Key | Code default | Effect here | Source |
|---|---|---|---|
| `channels.enable` | off | Channel destinations need it, at save time and at run time | `backend/open_webui/config.py:2028`; `backend/open_webui/routers/automations.py:114`; `backend/open_webui/utils/automations.py:260` |
| `channels.model_response_mode` | `thread` | Whether a channel run's reply goes in a thread or in the channel | `backend/open_webui/config.py:2030`; `backend/open_webui/utils/automations.py:280-284` |
| `ui.enable_user_webhooks` and permission `features.webhooks` | off, off | Needed before reminders can reach a personal notification target | `backend/open_webui/utils/notifications.py:393-395`; `src/lib/utils/settings-access.ts:16-18` |
| `subagents.enable` | off | Needed before the model is offered the `timer` tool | `builtin-native-tools.md` section 3.2 |
| `web.search.enable`, `image_generation.enable` | off, off | A run turns on a model's default web search or image generation only when these are on | `backend/open_webui/utils/automations.py:186-195` |
| `chat.tool_permissions.enable` | (see `builtin-native-tools.md`) | Has no effect on automation runs, which always use full access | `backend/open_webui/main.py:1254-1264` |

### 7.2 Environment-Only Settings

Read once, when the server process loads `backend/open_webui/utils/automations.py`; they are not
in `env.py`, are not stored, apply per process and need a restart to change. Because they are
converted to whole numbers when the module loads, a value that is not a whole number stops the
application from starting.

| Variable | Default | Effect | Source |
|---|---|---|---|
| `SCHEDULER_POLL_INTERVAL` (older name `AUTOMATION_POLL_INTERVAL`, read only when the new one is unset) | 10 seconds | Gap between automation and calendar-reminder checks, plus 0 to 2 seconds of random jitter | `backend/open_webui/utils/automations.py:53`, `:101-102` |
| `TIMER_POLL_INTERVAL` | 1 second | Gap between timer checks; also the loop's sleep, never less than 1 second | `:54`, `:99`, `:126` |
| `CALENDAR_ALERT_LOOKAHEAD_MINUTES` | 10 minutes | Reminder lead time for events without their own setting. The module's description says the default is 5; the code uses 10 | `:15`, `:55`, `:547` |

### 7.3 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Time allowed to evaluate a rule | 2 seconds, in a separate worker process | `backend/open_webui/utils/recurrence.py:13`, `:97-103` |
| Rules per schedule | One `RRULE` line; `EXRULE` refused | `backend/open_webui/utils/recurrence.py:42-49` |
| Automations claimed per check | 10 (the rest wait for the next check) | `backend/open_webui/utils/automations.py:108` |
| Timers claimed per check | 10 | `backend/open_webui/utils/automations.py:93` |
| Automations per list page | 30 | `backend/open_webui/routers/automations.py:37` |
| Run history page | 50 | `backend/open_webui/routers/automations.py:393`; `src/lib/components/automations/AutomationEditor.svelte:212` |
| Next-run preview | 5 times | `backend/open_webui/utils/recurrence.py:142` |
| Run error text | 4,000 characters (timer reply errors 500) | `backend/open_webui/utils/automations.py:522`; `backend/open_webui/utils/timers.py:419` |
| Shortest event recurrence | 1 day (86,400 seconds) | `backend/open_webui/models/calendar.py:30` |
| Reminder search window | 60 minutes ahead, about 15 seconds behind | `backend/open_webui/models/calendar.py:736-739`; `backend/open_webui/utils/automations.py:548-550` |
| Occurrences computed per recurring event per view | 5,000 | `backend/open_webui/utils/calendar.py:22` |
| Past automation runs shown per calendar view | 500 | `backend/open_webui/models/automations.py:437` |
| Event search page | 30 | `backend/open_webui/routers/calendar.py:295` |
| Reminder choices in the form | none, at the time, 5, 10, 15, 30 or 60 minutes before | `src/lib/components/calendar/CalendarEventModal.svelte:265-276` |
| Toast durations | Reminder 30 seconds; background-reply toast 15 seconds | `src/routes/+layout.svelte:616`, `:778` |

## 8. Cron Jobs and Background Processes

There is no crontab and no separate worker. Everything time-based in this area runs inside one
asyncio task, `scheduler_worker_loop`, which `lifespan` starts in **every** server process
(`backend/open_webui/main.py:403-405`) and cancels at shutdown (`:494`). At start it logs
`Scheduler worker started (timer poll interval: {TIMER_POLL_INTERVAL}s, scheduler poll interval: {SCHEDULER_POLL_INTERVAL}s)`
(`backend/open_webui/utils/automations.py:79-83`). The older name `automation_worker_loop` is only
an alias kept for old imports; nothing starts it (`:63-66`; the generated inventory lists both names).

### 8.1 What One Loop Does

| Step | How often | Condition | What happens | Source |
|---|---|---|---|---|
| Timers | Every `TIMER_POLL_INTERVAL` seconds (default 1, never less than 1) | Always; there is no switch for timers in the loop | Claim up to 10 due timers and start each in its own task | `backend/open_webui/utils/automations.py:89-99`, `:126` |
| Automations | Every `SCHEDULER_POLL_INTERVAL` seconds (default 10) plus 0 to 2 seconds of jitter | `automations.enable` on | Claim up to 10 due active automations (next time moved forward first), start each run in its own task, log `Claimed {n} due automation(s)` | `:101-114`; `backend/open_webui/models/automations.py:289-340` |
| Calendar reminders | Same as automations | `calendar.enable` on | Find events due for a reminder, alert and stamp them | `:116-121`, `:537-614` |
| Errors | — | — | Each step catches its own errors and logs `Scheduler: timer error`, `Scheduler: automation error` or `Scheduler: calendar alert error`; the loop keeps going (`Scheduler worker error` for anything else) | `:95-96`, `:113-114`, `:120-121`, `:123-124` |

Each automation run, timer firing and **Run now** is a separate background task in the process that
claimed or received it, so a slow model reply does not hold up the loop
(`backend/open_webui/utils/automations.py:94`, `:112`; `backend/open_webui/routers/automations.py:344`).
Rule evaluation itself happens in a short-lived separate process with a 2-second limit
(`backend/open_webui/utils/recurrence.py:97-103`).

### 8.2 Timing a Person Can Expect

- A scheduled run starts between 0 and about 12 seconds after its due time (poll plus jitter),
  and daily, weekly and monthly rules without a start line can be due up to a minute after the
  chosen minute (section 4.2). A run that waits behind ten others in the same check waits for the
  next check.
- When an automation is due while the server is down, while **Automations** is switched off, or
  while the rule cannot be evaluated, nothing is recorded; once the server and switch are back it
  runs **once** at the next check (catch-up) and the next time is worked out from then
  (`backend/open_webui/models/automations.py:298-336`).
- Paused automations are not caught up when resumed (section 5.4).
- Reminders are checked on the same cycle; a reminder set for "at time of event" arrives up to
  about 12 seconds after the start (section 5.13).

### 8.3 Several Workers, Replicas and the Database

| Situation | What the code does | Source |
|---|---|---|
| Several server processes or replicas | Every one runs its own loop; the random jitter spreads their checks | `backend/open_webui/main.py:403-405`; `backend/open_webui/utils/automations.py:101-102` |
| PostgreSQL | Due automations and timers are claimed with row locks that other processes skip (`FOR UPDATE SKIP LOCKED`), so each run is taken by one process | `backend/open_webui/models/automations.py:308-309`; `backend/open_webui/utils/timers.py:181-182` |
| SQLite (the default) | No row locks are taken; the code relies on moving the next time forward before running. Whether two processes can claim the same automation or timer at the same moment is **not established by the code** (section 14). `CLAUDE.md` already requires PostgreSQL for more than one worker | `backend/open_webui/models/automations.py:290-296`, `:308-309`; `CLAUDE.md` (Deployment) |
| Calendar reminders with several processes | Not claimed: each process reads due events, alerts, then stamps them. Two processes checking at the same moment could both send the same reminder (read from code; not confirmed) | `backend/open_webui/utils/automations.py:552-592` |
| Busy-chat check for timers | Uses Redis when configured; without Redis each process knows only its own replies, so a timer could fire into a chat that another process is still answering | `backend/open_webui/utils/timers.py:295`; `backend/open_webui/tasks.py:190-196`, `:312-315` |
| Per-timer locks | Held in each process's memory | `backend/open_webui/utils/timers.py:36`, `:231-232` |

### 8.4 Happens at Save Time, Not in the Background

- The next run time is computed when an automation is created, saved, resumed, and when the
  scheduler claims it (`backend/open_webui/routers/automations.py:229`, `:289`, `:316`;
  `backend/open_webui/models/automations.py:330`).
- Rule validation, the count limit and the interval limit are checked when saving
  (`backend/open_webui/routers/automations.py:218-226`, `:278-286`).
- Calendar occurrences and the Scheduled Tasks entries are computed when the calendar is viewed
  (`backend/open_webui/routers/calendar.py:184-265`).
- Timers are cancelled when the chat is read or a message is sent (section 5.14).
- Changing a person's time zone (the browser reports it at each app load) affects their next runs
  only when each automation's next time is next computed, that is after its next run or the next
  save (`backend/open_webui/models/automations.py:317-335`; `src/routes/+layout.svelte:1293-1297`).

## 9. Notifications and Emails

The application sends **no email** (`ground-truth.md`, Contacts). This area reaches people through
the browser (socket messages, toasts, browser notifications), personal notification targets
(webhooks) and application events. Delivery mechanics in general are in
`notifications-webhooks-events-and-banners.md`.

### 9.1 In the Browser

| Trigger | Socket message (to the person's sessions, room `user:{id}`) | What the person sees | Source |
|---|---|---|---|
| A chat-destination run creates its chat | `events` with `chat:list` | The chat list refreshes and shows the new chat | `backend/open_webui/utils/automations.py:460-471` |
| The run's reply finishes while the person is on another page or tab | Normal chat events | Toast with the automation's name and the start of the reply (15 seconds; click opens the chat); browser notification `{title} / {WEBUI_NAME}` in the most recent tab if **Browser Notifications** is on | `src/routes/+layout.svelte:735-781` |
| A run finishes or a channel run is posted | `automation:result` (`automation_id`, `name`, `chat_id`, `status`) | Nothing: no part of the interface listens for this message | `backend/open_webui/utils/automations.py:321-333`, `:497-509` |
| A calendar reminder is due | `events` with `calendar:alert` (`event_id`, `title`, `description`, `start_at`, `minutes_until`, `calendar_id`, `location`) | Toast with the title and `Starting now` / `Starting in 1 minute` / `Starting in {{count}} minutes` (30 seconds; click opens `/calendar`); browser notification `{title} / {WEBUI_NAME}` with the same text when **Browser Notifications** is on | `backend/open_webui/utils/automations.py:566-585`; `src/routes/+layout.svelte:600-628` |
| A timer fires | `events` with `chat:reload` for the parent chat | The chat reloads with the timer's prompt and the new reply | `backend/open_webui/utils/timers.py:367-375` |

Browser messages reach only sessions that are open at that moment; nothing is queued for later.
**Browser Notifications** is a personal switch in Settings › **Notifications**; turning it on asks
the browser for permission and, when refused, shows
`Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.`
(`src/lib/components/chat/Settings/Notifications.svelte:59-77`, `:194-209`;
`src/lib/i18n/locales/en-US/translation.json:2996`, `:2999`).

### 9.2 Personal Notification Targets (Webhooks)

When an admin has switched on user webhooks (`ui.enable_user_webhooks`, code default off) and,
for non-admins, granted `features.webhooks` (code default off), a person can add **Notification
Targets** in Settings › Notifications and choose which events each target receives
(`src/lib/utils/settings-access.ts:16-18`; `src/lib/components/chat/Settings/Notifications.svelte:54-58`, `:228-245`).
The event list comes from the server and includes **Calendar alert** ("A calendar event alert was
triggered."), **Chat finished** and **Chat failed** (`backend/open_webui/utils/notifications.py:223-231`;
`backend/open_webui/events.py:595-599`, `:669-675`).

| Event | Sent to | Text posted | Condition | Source |
|---|---|---|---|---|
| `calendar.alert` | The event's creator | `**{title}**` and `starting in {minutes} min` or `starting now` | Target enabled and subscribed; with delivery `away` (the default) only when the person has not been active in the last 3 minutes | `backend/open_webui/utils/automations.py:596-614`; `backend/open_webui/utils/notifications.py:322-336`, `:393-417`; `backend/open_webui/models/users.py:918-925` |
| `chat.finished`, `chat.failed` | The chat's owner, also for chats created by automation runs (saved chats) | The chat title and the reply, or the failure | As above | `backend/open_webui/utils/middleware.py:206-232`, `:4387-4405`; `backend/open_webui/utils/notifications.py:267-302` |

Automation events (`automation.*`) are not notification events, so a personal target is told about
an automation only through the chat events of its run (`backend/open_webui/events.py:669-675`).

### 9.3 Application Events

Each action publishes an event to the admin's event webhooks (Admin Settings, see
`notifications-webhooks-events-and-banners.md`) and to installed **Event** functions
(`functions-pipes-filters-actions-and-pipelines.md`). The webhook message is the event's message
followed by the subject id in brackets (`backend/open_webui/events.py:1034-1059`, `:1103-1171`).
Event payloads carry the names of the person's automations and calendars, event titles, and for
reminders the event's description and location; treat them as personal data.

| Event | Message | Published when | Source |
|---|---|---|---|
| `automation.created` | `Automation created` | Create on the Automations page or through the API | `backend/open_webui/events.py:600-602`; `backend/open_webui/routers/automations.py:231-237` |
| `automation.updated` | `Automation updated` | Save | `backend/open_webui/events.py:603-605`; `:291-297` |
| `automation.enabled` / `automation.disabled` | `Automation enabled` / `Automation disabled` | Resume / pause | `backend/open_webui/events.py:606-611`; `:318-325` |
| `automation.deleted` | `Automation deleted` | Delete | `backend/open_webui/events.py:612-614`; `:372-379` |
| `automation.run_started` | `Automation run started` | **Run now** only (scheduled runs do not publish it) | `backend/open_webui/events.py:615-617`; `:345-351` |
| `automation.run_completed` | `Automation run completed` | A run was recorded as `success` | `backend/open_webui/events.py:618-620`; `backend/open_webui/utils/automations.py:336-342`, `:512-518` |
| `automation.run_failed` | `Automation run failed` | A run was recorded as `error` (with the error text) | `backend/open_webui/events.py:621-623`; `backend/open_webui/utils/automations.py:356-361`, `:373-379`, `:451-457`, `:524-529` |
| `calendar.created`, `calendar.updated`, `calendar.deleted`, `calendar.default_updated` | `Calendar created`, `Calendar updated`, `Calendar deleted`, `Calendar default updated` | Calendar changes | `backend/open_webui/events.py:567-580`; `backend/open_webui/routers/calendar.py:128-134`, `:431-437`, `:462-468`, `:478-484` |
| `calendar.event.created`, `calendar.event.updated`, `calendar.event.deleted`, `calendar.event.rsvp_updated` | `Calendar Event created`, `Calendar Event updated`, `Calendar Event deleted`, `Calendar Event rsvp updated` | Event changes and answers | `backend/open_webui/events.py:581-594`; `backend/open_webui/routers/calendar.py:280-286`, `:337-343`, `:359-365`, `:381-387` |
| `calendar.alert` | `Calendar alert` (the posted message is the event title) | A reminder is sent (source `scheduler`) | `backend/open_webui/events.py:595-599`; `backend/open_webui/utils/automations.py:599-612` |

Changes made by the model's built-in automation and calendar tools do **not** publish these
change events: the tools write to the tables directly and `backend/open_webui/tools/builtin.py`
has no `publish_event` call for them (its only one is for notes, `:96`; `builtin-native-tools.md`
section 9.3). Runs of automations the model created still publish the run events above, because
runs go through the scheduler.

## 10. Error, Warning and Notice Messages (Verbatim)

Server refusals reach the person as a red toast that prints the server's text: the API helpers
throw the response's `detail` and the pages show it with `toast.error`
(`src/lib/apis/automations/index.ts:91-102`; `src/lib/apis/calendar/index.ts:86-97`). A refusal
from FastAPI's own form validation has a list as its `detail`, which such a toast prints as
[object Object] (for example a hand-edited import file missing a field). An error the page raises
itself prints with an `Error: ` prefix. Placeholders follow the source's variable names.

### 10.1 Automations Page and Form (Front End)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Name, prompt, and model are required` | Error (toast) | `src/lib/components/AutomationModal.svelte:46-48` | **Create** or **Save** with an empty title, prompt or model | Fill in all three | None |
| `Channel is required` | Error (toast) | `src/lib/components/AutomationModal.svelte:50-52` | Destination **Channel** chosen without picking one | Pick a channel, or choose **New chat** | If no channel is listed, channels may be off or the person is in none (section 7.1) |
| `Scheduled time must be in the future` | Error (toast) | `src/lib/components/AutomationModal.svelte:54-59` | **Once** with a date and time not after the browser's current time | Choose a later time | Check the date: in the evening the default date can be tomorrow's (section 4.2) |
| `Automation created` | Success (toast) | `src/lib/components/AutomationModal.svelte:82` | Saved a new automation | None | None |
| `Automation updated` | Success (toast) | `src/lib/components/AutomationModal.svelte:77` | Saved changes | None | None |
| `Failed to save` | Error (toast, fallback) | `src/lib/components/AutomationModal.svelte:87` | Only if a save error had no text; in practice the server's text is shown instead | Retry | Escalate with the time |
| `Automation triggered` | Success (toast) | `src/routes/(app)/automations/+page.svelte:201`; `src/lib/components/automations/AutomationEditor.svelte:170` | **Run Now** / **Run now** accepted; the run has only **started** | Check **Runs** and open the chat | Section 5.8 |
| `Deleted {name}` | Success (toast) | `src/routes/(app)/automations/+page.svelte:211`; `src/lib/components/automations/AutomationEditor.svelte:195` | Automation deleted (key `Deleted {{name}}`) | None; deletion is permanent | None |
| `Delete automation?` with `This will delete {name}.` | Confirmation dialog | `src/routes/(app)/automations/+page.svelte:414-424`; `src/lib/components/automations/AutomationEditor.svelte:269-277` | Delete chosen from the menu or editor (not with Shift held) | **Confirm** or **Cancel** | None |
| `Imported automations successfully` | Success (toast) | `src/routes/(app)/automations/+page.svelte:436-438` | Import finished without an error. Also shown when the file contained no automations list, in which case nothing was created | Check the list | Ask for the file's structure if nothing appeared |
| `Invalid JSON format` | Error (toast, shown as `Error: ` plus this text) | `src/routes/(app)/automations/+page.svelte:289-291`, `:439-441` | The file's `automations` entry is not a list | Use a file made by **Export JSON** | None |
| `No automations found` with `Create scheduled prompts that run automatically on a recurring basis.` | Notice (empty list) | `src/routes/(app)/automations/+page.svelte:575-587` | The person has no automations | Choose **Create** | None |
| `No results found` with `Try adjusting your search or filter to find what you are looking for.` | Notice (empty list) | `src/routes/(app)/automations/+page.svelte:579-584` | Search or filter matched nothing | Clear the search or set **All** | None |
| `No runs yet` | Notice | `src/lib/components/automations/AutomationEditor.svelte:365-368` | No `automation_run` rows for this automation | Wait for the next run or **Run now** | If a run was expected, section 11.1 |
| `Not scheduled` | Notice (Next run) | `src/lib/components/automations/AutomationEditor.svelte:90-95` | No next run: paused, or a one-time automation that has already run | Resume, or edit the schedule | None |
| `Never` | Notice (Last run) | `src/routes/(app)/automations/+page.svelte:226-230`, `:618-621`; `src/lib/components/automations/AutomationEditor.svelte:340` | The scheduler has never claimed it (manual runs do not count) | None | Compare with **Runs** |
| `Select model` / `No results found` | Notice (model menu) | `src/lib/components/automations/ModelDropdown.svelte:23-25`, `:123-126` | No model chosen yet / search matched no model, or the person has no models | Pick a model | `workspace-models-and-model-access.md` |
| `Choose channel` / `No channels` / `No folders` | Notice (destination menu) | `src/lib/components/automations/DestinationDropdown.svelte:63-70`, `:258-261`, `:305-308` | Channel destination without a channel / no channels or folders to offer | Pick one, or use **New chat** | Channels need `channels.enable` |
| `Warning: Enabling this will allow users to run scheduled prompts automatically.` | Warning (tooltip, admin) | `src/lib/components/admin/Users/Groups/Permissions.svelte:1114-1127` | Hovering the **Automations** permission | None | None |

### 10.2 Automation API Refusals (Shown in Toasts)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:45-58`; `backend/open_webui/constants.py:69` | Any automation endpoint while **Automations** is off for the site, or for a non-admin without `features.automations`. The pages normally send such people to `/` first, so it is mostly seen when the switch changes while a page is open | Reload; ask an admin about access | Site switch and the person's groups (section 3.1) |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/automations.py:61-66`, `:98-106`, `:109-125`; `backend/open_webui/constants.py:78` | The automation does not exist or belongs to someone else (admins included); the chosen folder is not the person's; a channel destination while channels are off, without a channel, or for a deleted channel | Use their own automation; pick another destination | On `/automations/{id}` the page then returns to the list |
| `Automation limit reached ({max_count})` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:74-83`; `backend/open_webui/constants.py:116` | A non-admin creating (or importing) when they already own `automations.max_count` automations, paused ones included | Delete unused automations | Live `automations.max_count` value (TO BE CONFIRMED) |
| `Schedule too frequent. Minimum interval is {min_interval} seconds.` | Error (HTTP 400) | `backend/open_webui/routers/automations.py:85-95`; `backend/open_webui/constants.py:117` | A non-admin saving a rule whose next two runs are closer than `automations.min_interval` seconds | Choose a less frequent schedule | Live `automations.min_interval` value |
| `Something went wrong :/` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:127-144`; `backend/open_webui/constants.py:16-23` | Channel destination when the person lacks `features.channels`, is not a member of a group or direct-message channel, or has no write access to the channel | Choose a channel they can post in | `channels-and-direct-messages.md` |
| `Invalid RRULE: {err}` | Error (HTTP 400) | `backend/open_webui/utils/recurrence.py:116-123`; `backend/open_webui/constants.py:118`; `backend/open_webui/routers/automations.py:218-224`, `:278-284` | The rule cannot be read. `{err}` is the reason: one of the three messages below, or the python-dateutil library's own text, for example invalid 'FREQ': SOMETIMES or hour must be in 0..23 | Fix the custom rule, or use a preset | Ask for the exact rule text |
| `EXRULE is not supported in recurrence rules` | Error (inside `Invalid RRULE: {err}`) | `backend/open_webui/utils/recurrence.py:42-44` | The rule contains `EXRULE` | Remove it | None |
| `only one RRULE is supported per recurrence rule` | Error (inside `Invalid RRULE: {err}`) | `backend/open_webui/utils/recurrence.py:46-49` | More than one `RRULE` line | Keep one | None |
| `RRULE INTERVAL must be a positive integer` | Error (inside `Invalid RRULE: {err}`) | `backend/open_webui/utils/recurrence.py:68-69` | `INTERVAL` below 1 on an hourly, minutely or secondly rule | Use 1 or more | None |
| `RRULE has no future occurrences` | Error (HTTP 400) | `backend/open_webui/utils/recurrence.py:124-125`; `backend/open_webui/constants.py:119` | The rule never runs again after now, judged in the person's **stored** time zone (or server time). A **Once** time the browser accepted can still be refused when the stored zone differs from the browser's | Choose a later time | Compare the person's stored time zone with their location (section 11.3) |
| `RRULE with COUNT requires an explicit DTSTART line to anchor the occurrence window` | Error (HTTP 400) | `backend/open_webui/utils/recurrence.py:113-115`; `backend/open_webui/constants.py:120-122` | A custom rule with `COUNT=` but no `DTSTART` line | Add a `DTSTART:` line or remove `COUNT` | None |
| `Schedule took too long to evaluate; simplify its recurrence rule.` | Error (HTTP 400) | `backend/open_webui/utils/recurrence.py:97-103`; `backend/open_webui/routers/automations.py:218-224` | Working out the next run took more than 2 seconds (an unusual custom rule, or a busy server) | Simplify the rule; retry | Escalate if presets also fail (server load) |

### 10.3 Run Errors (Runs List and Scheduled Tasks)

Shown in red beside a run on the automation's page and as the description of a failed past run on
the calendar (`src/lib/components/automations/AutomationEditor.svelte:399-403`;
`backend/open_webui/routers/calendar.py:246`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `User not found` | Run error | `backend/open_webui/utils/automations.py:353-362` | The owner's account no longer exists; nobody can see this in the interface, because only the owner can open the automation | None | Orphaned automations of deleted users keep failing at every scheduled time (section 6.7) |
| `Owner no longer permitted to run automations` | Run error | `backend/open_webui/utils/automations.py:364-380` | At run time the owner is not a `user` or `admin` (for example set to `pending`), or no longer holds `features.automations` | Ask an admin about the permission | The person's role and groups |
| `Failed to create chat` | Run error | `backend/open_webui/utils/automations.py:448-458` | The run's new chat could not be saved | Retry with **Run now** | Escalate with the run time (database problem) |
| `Channel not found` | Run error | `backend/open_webui/utils/automations.py:258-261` | Channel destination while **Channels** is off for the site, or no channel id stored | Change the destination | `channels.enable` |
| `Model not found` (recorded as `400: Model not found`) | Run error | `backend/open_webui/main.py:1128-1129`, `:1150-1161`, `:1638-1645`; `backend/open_webui/utils/models.py:465-520`; `backend/open_webui/utils/automations.py:520-529` | The automation's model no longer exists, or the (non-admin) owner can no longer use it | Edit the automation and pick an available model | `workspace-models-and-model-access.md` |
| `We could not find what you're looking for :/` or `Something went wrong :/` (recorded with `404: ` or `403: ` in front) | Run error | `backend/open_webui/routers/channels.py:1137-1160`; `backend/open_webui/main.py:1307-1359` | Channel run: the channel was deleted, or the owner may no longer post in it | Change the destination | Channel membership and access |
| Any other text, possibly with an HTTP status in front | Run error | `backend/open_webui/utils/automations.py:520-529` | Any other failure before the reply started; cut to 4,000 characters | Retry with **Run now** | Escalate with the automation name, run time and text |

### 10.4 Calendar Page and Forms (Front End)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Title is required` | Error (toast) | `src/lib/components/calendar/CalendarEventModal.svelte:119-122` | Event saved without a title | Add a title | None |
| `Date is required` | Error (toast) | `src/lib/components/calendar/CalendarEventModal.svelte:124-127` | Event saved without a date | Pick a date | None |
| `Event created` | Success (toast) | `src/lib/components/calendar/CalendarEventModal.svelte:168-172` | New event saved | None | None |
| `Event updated` | Success (toast) | `src/lib/components/calendar/CalendarEventModal.svelte:139-154` | Changes saved (for a recurring event, the whole series) | None | Section 5.11 |
| `Event deleted` | Success (toast) | `src/lib/components/calendar/CalendarEventModal.svelte:182-189` | Event deleted (for a recurring event, the whole series) | None; no undo | None |
| `Delete Event` with `This action cannot be undone. Do you wish to continue?` | Confirmation dialog | `src/lib/components/calendar/CalendarEventModal.svelte:347-351` | **Delete** in the event form | **Confirm** or **Cancel** | None |
| `Name is required` | Error (toast) | `src/lib/components/calendar/CreateCalendarModal.svelte:39-43` | New calendar without a name | Type a name | None |
| `Calendar created` | Success (toast) | `src/lib/components/calendar/CreateCalendarModal.svelte:51-55` | Calendar created | None | None |
| `Delete Calendar` with `This will permanently delete the calendar "{name}" and all its events. This action cannot be undone.` | Confirmation dialog | `src/lib/components/calendar/CalendarSidebar.svelte:94-103` | Bin beside a calendar | **Delete** or **Cancel** | None |
| `Calendar deleted` | Success (toast) | `src/routes/(app)/calendar/+page.svelte:116-121` | Calendar and its events deleted | None; no undo | None |
| `Failed to delete calendar` | Error (toast) | `src/routes/(app)/calendar/+page.svelte:122-125` | The server answered without confirming the deletion | Retry | Escalate with the time |

The calendar page shows nothing at all when its calendar list fails to load; only the event load
shows the server's refusal as a toast (`src/routes/(app)/calendar/+page.svelte:83-100`).

### 10.5 Calendar API Refusals (Shown in Toasts)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:37-49`; `backend/open_webui/constants.py:69` | **Calendar** off for the site, or a non-admin without `features.calendar`. On `/calendar` it appears as a toast over an empty calendar | Ask an admin about access | Section 3.1 |
| `Calendar not found` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:62-66`, `:472-477` | Unknown calendar id, including an event saved while no calendar was loaded; making someone else's calendar the default (API) | Reload the page | If the list is always empty, check access (section 11.5) |
| `Access denied` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:62-79` | No read access (opening) or write access (adding, changing, deleting events; deleting a calendar) through sharing | Use own calendar, or ask the owner for write access | Calendar sharing is API-only (section 2.4) |
| `Event not found` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:302-307`, `:319-321`, `:350-352` | The event was deleted (for example by someone else with write access) | Reload | None |
| `Failed to update` | Error (HTTP 500) | `backend/open_webui/routers/calendar.py:335-336`, `:428-430` | The event or calendar vanished during the update | Reload and retry | Escalate if repeated |
| `Failed to delete` | Error (HTTP 500) | `backend/open_webui/routers/calendar.py:356-358`, `:459-461`; `backend/open_webui/models/calendar.py:393-423`, `:774-782` | The deletion raised an error (logged for calendars as `Failed to delete calendar {id}: {e}`) | Retry | Escalate with the time; check the server log |
| `Only owner can delete calendar` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:451-453` | Bin used on a calendar shared with write access | Ask the owner | None |
| `Default calendar cannot be deleted` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:455-457` | API attempt on the default calendar (the interface hides the bin) | None | None |
| `System calendars cannot be deleted` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:445-447` | API attempt on Scheduled Tasks | None | None |
| `Only owner can manage sharing` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:410-412` | API: someone with write access but not the owner changed sharing | Ask the owner | None |
| `Invalid date format. Use ISO 8601 (e.g. 2026-04-01T00:00:00)` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:165-169` | API: unreadable `start` or `end` when listing events | Fix the request | None |
| `Invalid status` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:375-376` | API: invitation answer other than `accepted`, `declined`, `tentative` or `pending` | Fix the request | None |
| `Not an attendee of this event` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:378-380` | API: answering an invitation one did not receive | None | None |
| `Recurring events cannot repeat more often than daily` | Error (HTTP 422) | `backend/open_webui/models/calendar.py:182-193`; `backend/open_webui/constants.py:123`; `backend/open_webui/routers/calendar.py:276-279`, `:331-334` | API (or a custom rule) repeating more often than once a day; the form's own choices always pass | Use Daily or a longer repeat, or make an automation instead | None |
| `Schedule took too long to evaluate; simplify its recurrence rule.` | Error (HTTP 422) | `backend/open_webui/utils/recurrence.py:97-103`; `backend/open_webui/models/calendar.py:186-189` | The event's rule took more than 2 seconds to evaluate | Retry; simplify the rule | Escalate if the form's own choices fail (server load) |
| `Invalid RRULE: {err}` | Error (HTTP 422) | `backend/open_webui/models/calendar.py:190-191` | An unusual failure while reading an event's rule. Most unreadable rules instead show the library's own message without this prefix, because those errors pass straight through (`:188-189`; the evaluation worker hands errors back unchanged, `.venv/lib/python3.12/site-packages/anyio/to_process.py:95-98`) | Use one of the form's choices | Ask for the rule text |

### 10.6 Reminders

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Starting now` | Notice (toast, browser notification) | `src/routes/+layout.svelte:600-628` | Reminder at or after the start | Click to open the calendar | None |
| `Starting in 1 minute` | Notice | `src/routes/+layout.svelte:605` | Reminder one minute before | As above | None |
| `Starting in {count} minutes` | Notice | `src/routes/+layout.svelte:606`; `src/lib/i18n/locales/en-US/translation.json:3128-3129` | Reminder with more than one minute to go (key `Starting in {{count}} minutes`) | As above | None |
| `**{title}**` then `starting in {minutes_until} min` or `starting now` | Notice (personal webhook) | `backend/open_webui/utils/automations.py:598`; `backend/open_webui/utils/notifications.py:322-336` | Reminder delivered to a personal notification target | None | Section 9.2 |
| `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.` | Error (toast) | `src/lib/components/chat/Settings/Notifications.svelte:59-72` | **Browser Notifications** switched on but the browser refused permission | Allow notifications for the site in the browser | Browser setting, not an application fault |

### 10.7 Timers

Timer failures are written only to the hidden timer chat (`meta.timer_error`); the person sees no
message (`backend/open_webui/utils/timers.py:422-429`; `builtin-native-tools.md` 5.8).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `parent chat no longer exists` | Internal timer state | `backend/open_webui/utils/timers.py:245-249`, `:286-294` | The chat the timer belonged to is gone | None | None |
| `timer task message is missing` | Internal timer state | `backend/open_webui/utils/timers.py:251-255` | The hidden chat lost its prompt | None | Escalate if frequent |
| `timer user no longer exists` | Internal timer state | `backend/open_webui/utils/timers.py:257-260` | Owner account deleted | None | None |
| `owner no longer permitted to run timers` | Internal timer state | `backend/open_webui/utils/timers.py:262-265` | Owner is no longer `user` or `admin` | None | Role |
| `model context is missing` | Internal timer state | `backend/open_webui/utils/timers.py:267-271` | No model recorded with the timer | None | None |
| The reply's error text (up to 500 characters) | Internal timer state | `backend/open_webui/utils/timers.py:415-419` | The fired reply could not start | Ask again in the chat | Server log `Timer {timer_id} completion failed` |
| `Error: prompt must not be empty.`, `Error: chat and user context are required.`, `Error: model context is required.`, `Error: timers are unavailable for direct connections.`, `Error: cancel_on accepts only chat.read and chat.user_message.`, `Error: failed to create timer.` | Tool result (to the model) | `backend/open_webui/utils/timers.py:80-101`, `:158-159` | The model's `timer` call was refused | Rephrase the request | `builtin-native-tools.md` 10.4 |
| `at must be in the future.`, `at must be a relative time such as 10s or in 10 seconds, or an RFC 3339 timestamp with a timezone.`, `absolute at values must include an explicit timezone.` (each after `Error: `) | Tool result (to the model) | `backend/open_webui/utils/timers.py:39-66`, `:86-89` | The time the model gave could not be used | As above | As above |

### 10.8 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Meaning |
|---|---|---|---|
| `Scheduler worker started (timer poll interval: %ss, scheduler poll interval: %ss)` | Log (info) | `backend/open_webui/utils/automations.py:79-83` | The loop started in this process, with its two intervals |
| `Claimed %s due automation(s)` | Log (info) | `backend/open_webui/utils/automations.py:109-110` | This process took that many runs in one check |
| `Automation {automation.id} failed` | Log (exception) | `backend/open_webui/utils/automations.py:520-521` | A run failed; the stack trace follows |
| `Skipping automation %s: recurrence evaluation timed out` | Log (warning) | `backend/open_webui/models/automations.py:331-333` | The rule could not be evaluated in 2 seconds; the run was not taken and will be retried at the next check |
| `Unknown timezone %r — falling back to server time` | Log (warning) | `backend/open_webui/utils/recurrence.py:27-33` | A person's stored time zone is not a known zone name; their schedules use server time |
| `Scheduler: timer error`, `Scheduler: automation error`, `Scheduler: calendar alert error`, `Scheduler worker error` | Log (exception) | `backend/open_webui/utils/automations.py:95-96`, `:113-114`, `:120-121`, `:123-124` | That step failed in this check; the loop continues |
| `Failed to compute automation events: {e}` | Log (warning) | `backend/open_webui/routers/calendar.py:266-267` | Scheduled Tasks entries could not be built; the calendar shows the other events |
| `EXRULE is not supported for event {id}: {rrule}`, `Failed to parse RRULE for event {id}: {rrule}` | Log (warning) | `backend/open_webui/utils/calendar.py:32-34`, `:49-54` | A stored event's rule could not be expanded; the event shows once, at its stored start |
| `Failed to mark event %s as alerted`, `Failed to send notification for calendar alert %s` | Log (debug) | `backend/open_webui/utils/automations.py:588-594`, `:596-614` | The reminder stamp or the notification failed; a reminder whose stamp failed can be sent again at the next check |
| `Timer {timer_id} completion failed` | Log (exception) | `backend/open_webui/utils/timers.py:417-419` | A fired timer's reply could not start |
| `Terminal server {server_id} not found for CWD set`, `Failed to set terminal CWD to {cwd}: HTTP {resp.status} — {body[:200]}`, `Failed to set terminal CWD: {e}` | Log (warning) | `backend/open_webui/utils/automations.py:202-247` | From a helper that nothing calls in v0.11.4 (section 6.1); not expected in logs |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes settings, permissions, roles or anyone's data. Ask for the
automation's or event's **name**, the **time** the person expected, and a screenshot of the
automation page (Status, Schedule, Next run, Last run, Runs). Never ask for the prompt text or
the content of the chats it produced unless the person offers it; automation prompts and results
can contain personal or health information.

### 11.1 "My automation didn't run"

**Symptom.** No new chat or channel post at the expected time, or nothing in **Runs**.

**Likely causes, in order.**

1. It **did** run but the person looked in the wrong place: chat-destination runs create a **new
   chat** named after the automation each time (inside the chosen folder, if any), not a reply in
   an old chat (section 5.9).
2. The automation is **paused** (Status **Paused**, Next run **Not scheduled**), or it is a
   **Once** automation that has already run (section 4.1).
3. A run happened and **failed**: a red dot in **Runs** with a reason such as
   `Owner no longer permitted to run automations`, `400: Model not found` or `Channel not found`
   (section 10.3).
4. The run is recorded as `success` but the reply failed inside the chat (section 11.6).
5. **Automations** was switched off for the site, the server was down, or the person lost the
   `features.automations` permission at the time; nothing is recorded while the site switch is
   off or the server is down, and one catch-up run happens when they return (section 8.2).
6. It is scheduled for a different time than the person thinks (section 11.3).
7. The rule cannot be evaluated quickly enough; the server log shows
   `Skipping automation {id}: recurrence evaluation timed out` at every check (section 10.8).

**Diagnostic steps.**

1. Ask the person to open the automation (`/automations/{id}`) and read **Status**, **Next run**,
   **Last run** and the newest lines of **Runs**.
2. If **Runs** shows a green dot, ask them to use **View chat** (or **View channel**) and say
   whether an answer or an error is there.
3. If **Runs** shows a red dot, note the exact red text and match it in section 10.3.
4. If **Runs** is empty and **Last run** is **Never**, check that the person still sees
   **Automations** in their user menu (feature and permission) and whether others report the
   same (site-wide).
5. Compare **Next run** with the time the person expected.

**Resolution.** Explain where results appear; explain pause/resume and **Run now** (sections 5.4
and 5.5); for a model error, ask the person to edit the automation and choose a model they can
still use. Tier 1 does not turn features or permissions on.

**Escalation.** Send the automation's name and id (from the page address), the person's account
(email), the expected time with time zone, the **Runs** lines and red text. For site-wide
failures, ask the maintainer to check the server log for `Scheduler:` lines and `Claimed`
lines around that time, and the live `automations.enable` value.

### 11.2 "It ran twice"

**Symptom.** Two chats or posts from the same automation at about the same time, or two lines in
**Runs** close together.

**Likely causes, in order.**

1. **Run now** was used close to a scheduled run, or pressed more than once; each press starts a
   run and does not move the schedule (section 5.5).
2. There are **two automations** with the same instructions: a clone, a repeated import of the
   same file, or one created by the model through the `create_automation` tool as well as one
   made by hand (sections 5.6; `builtin-native-tools.md` 4.3).
3. A catch-up run after the server or the site switch came back, followed by the next regular
   run (section 8.2).
4. More than one server process on a SQLite database, where the code does not lock rows while
   claiming (section 8.3); whether this can produce a double run is not established.

**Diagnostic steps.**

1. Ask whether either run was a **Run now**; compare the two **Runs** times with the schedule.
2. Ask the person to search their Automations list for the automation's name or a word of its
   instructions and count matching rows.
3. Ask whether the service was unavailable shortly before the first run.

**Resolution.** Explain **Run now**; suggest deleting or pausing duplicate automations (the person
does this). If neither applies, escalate.

**Escalation.** Automation name and id, both run times, the account. Ask the maintainer how many
server processes or replicas run and whether the database is SQLite or PostgreSQL (deployment is
**TO BE CONFIRMED**, `ground-truth.md`, Environments).

### 11.3 "It ran at the wrong time"

**Symptom.** The run happened hours early or late, a day off, or a minute late.

**Likely causes, in order.**

1. **Time zone.** Schedules are read in the person's **stored** time zone, which the browser
   reports when the app loads. If none is stored, or it is unknown, the **server's local time** is
   used (often UTC). A person who used the app while travelling, or on a computer set to another
   zone, has that zone stored (section 4.1).
2. **One-time default date**: in the evening the **Once** date defaults to tomorrow (section 4.2).
3. **Catch-up run** after downtime or after **Automations** was switched back on (section 8.2).
4. **Rule shape**: **Hourly** runs at minute 0; **Weekly** with no day chosen repeats on the day it
   was saved; **Monthly** on the 29th to 31st skips shorter months; a custom `DTSTART` ending in
   `Z` or carrying a time zone is still read in the person's zone (sections 4.1 and 4.2).
5. **Normal delay**: up to about 12 seconds after the due minute, plus up to a minute for rules
   without a start line (section 8.2).
6. Daylight-saving changes, when the schedule falls back to server time on a server that does not
   follow the person's zone.

**Diagnostic steps.**

1. Ask for the time the person expected, the time it ran (from **Runs**, shown in their browser's
   zone), and the time zone their computer uses.
2. Ask them to open the automation and read **Schedule** and **Next run**; a **Next run** that is
   off by a whole number of hours points to a time-zone mismatch.
3. Check whether the run time matches a known outage or a recent change of the site switch.

**Resolution.** Explain the rule. If the computer's time zone was wrong, the person corrects it in
their operating system and reloads the app; the next run time is worked out again after the next
run or when they save the automation (section 8.4), so suggest saving it once. For **Once**,
re-check the date.

**Escalation.** Account, automation id, expected and actual times. The maintainer can check the
account's stored time zone and the server's time zone (both data, not visible in the interface).

### 11.4 "I don't see Automations (or Calendar) anywhere"

**Symptom.** No **Automations** or **Calendar** entry in the user menu or sidebar; going to
`/automations` returns to the home page; `/calendar` shows `401 Unauthorized`.

**Likely causes, in order.**

1. **Automations**: the person is not an admin and no group (or the defaults) grants
   `features.automations`, which is **off** in the code defaults (section 3.1).
2. The site switch **Automations** or **Calendar** is off (Admin Settings › General).
3. For **Calendar**, `features.calendar` was removed for the person's groups and defaults.
4. The entries are in the **user menu**, not pinned to the sidebar; they can be pinned with
   **Shift** held (section 2.2).

**Diagnostic steps.** Ask the person to open the user menu (their name at the bottom of the
sidebar) and look for the entries; ask whether colleagues in the same group see them.

**Resolution.** Show where the entries are and how to pin them. Access decisions belong to the
admins; tier 1 does not grant permissions.

**Escalation.** Account and which feature. Ask an admin to review **Default permissions** and the
person's groups, and the site switches (live values are data).

### 11.5 "I can't create an automation"

**Symptom.** **Create** shows an error, or nothing is saved.

**Likely causes, in order.**

1. A required field is missing: `Name, prompt, and model are required`, `Channel is required`.
2. The **Once** time is in the past: `Scheduled time must be in the future`, or the server's
   `RRULE has no future occurrences` when the stored time zone differs from the browser's.
3. A limit applies (non-admins): `Automation limit reached ({max_count})` (paused automations
   count; delete unused ones) or `Schedule too frequent. Minimum interval is {min_interval} seconds.`
4. A custom rule is wrong: `Invalid RRULE: {err}`, `RRULE with COUNT requires an explicit DTSTART line to anchor the occurrence window`,
   `Schedule took too long to evaluate; simplify its recurrence rule.`
5. The destination is refused: `We could not find what you're looking for :/` (folder or channel
   gone, channels switched off) or `Something went wrong :/` (no right to post in that channel).
6. The model menu is empty (`No results found`): the person can use no models (see
   `workspace-models-and-model-access.md`).

**Diagnostic steps.** Ask for the exact toast text and the chosen schedule and destination; match
the text in sections 10.1 and 10.2.

**Resolution.** Guide the fix for fields, time and rule; for limits, explain them and suggest
removing unused automations or choosing a less frequent schedule.

**Escalation.** If a preset schedule fails with an evaluation timeout, or a limit seems wrong,
send the account, the text and the time to the maintainer (live limit values are data).

### 11.6 "Runs shows a green dot but there's no answer"

**Symptom.** **Runs** shows `success`, but the chat has an error or an empty reply.

**Likely causes, in order.**

1. `success` means the reply was **started**; the model or provider then failed, and the error is
   shown on the reply in the chat (section 5.8).
2. The reply is still being written (long answers, slow model).
3. A tool the model used failed during the reply (runs have full tool access and do not pause for
   approval; `builtin-native-tools.md` 5.10).

**Diagnostic steps.** Ask the person to open **View chat** and read the reply's error, if any;
ask whether a normal chat with the same model works now.

**Resolution.** If the same model fails in normal chats, treat it as a model or provider problem
(`model-connections-openai-ollama-and-direct.md`); otherwise suggest **Run now** to retry.

**Escalation.** Automation id, run time, the reply's error text, the model name.

### 11.7 "Calendar reminders never arrive"

**Symptom.** No reminder toast or notification before an event.

**Likely causes, in order.**

1. **Reminder** is set to **None**, or the event was created through the API with `-1`.
2. The reminder **was already sent once**: each event is reminded once, and moving or editing it
   afterwards does not re-arm it (section 5.13).
3. It is a **later occurrence of a recurring event**: only the series' first start is reminded.
4. The person is **not the event's creator**: reminders go only to whoever created the event, not
   to attendees, other people sharing the calendar or the calendar's owner.
5. No app tab was open at the time: in-app reminders reach only open sessions; browser
   notifications also need **Browser Notifications** on, browser permission, and appear in the
   most recently active tab only (section 9.1).
6. A personal webhook target was expected: it needs user webhooks enabled by an admin, the
   `features.webhooks` permission, the target subscribed to **Calendar alert**, and, with the
   default delivery, the person away for 3 minutes (section 9.2).
7. **Calendar** is switched off for the site, or the server was down at the time (reminders more
   than about 15 seconds late are skipped).
8. An all-day event: its reminder is counted from midnight, so it came the evening before.

**Diagnostic steps.**

1. Ask the person to open the event and read **Reminder** and **Repeat**; ask whether they
   created it themselves and whether it was edited after an earlier reminder.
2. Ask whether the app was open in a tab at the time and whether **Browser Notifications** is on
   in Settings › Notifications.
3. Ask whether colleagues' reminders work (site-wide versus personal).

**Resolution.** Explain the once-only and creator-only rules. To get a fresh reminder for a moved
event, the person can create a new event (and delete the old one). For repeating reminders, an
automation or the model's `timer` tool may suit better (sections 5.2 and 5.14).

**Escalation.** If reminders fail for everyone, send the time window to the maintainer to check
the server log for `Scheduler: calendar alert error` and the live `calendar.enable` value.

### 11.8 "Recurring event won't save"

**Symptom.** Saving an event with **Repeat** shows an error.

**Likely causes, in order.**

1. The chosen calendar is shared with the person **read-only**: `Access denied`.
2. The repeat came from outside the form (API, a custom rule) and repeats more often than daily:
   `Recurring events cannot repeat more often than daily`.
3. The rule could not be evaluated in time: `Schedule took too long to evaluate; simplify its recurrence rule.`
4. The calendar list did not load (for example the feature was switched off while the page was
   open): `Calendar not found` or `401 Unauthorized`.

**Diagnostic steps.** Ask for the exact toast text and which calendar was selected in the form.

**Resolution.** Choose a calendar the person owns (normally `Personal`) or ask the calendar's
owner for write access. For anything more frequent than daily, suggest an automation or a
`timer` instead.

**Escalation.** If a built-in choice such as **Daily** fails with the evaluation message, send the
time and account to the maintainer (server load).

### 11.9 "I changed one occurrence and the earlier ones disappeared" or "Deleting one occurrence deleted them all"

**Symptom.** After editing or deleting one occurrence of a repeating event, the rest of the series
changed or vanished.

**Likely causes, in order.**

1. The form always edits the **whole series**; saving from an occurrence moves the series' start to
   that occurrence, and **Delete** removes the series (section 5.11).
2. The series had a custom recurrence (from the API) that the form showed as **No Repeat**; saving
   removed the recurrence.

**Diagnostic steps.** Ask which occurrence was opened and what was changed.

**Resolution.** Explain the behaviour. The person can recreate the series with the original start
date. Deleted events cannot be restored in the code.

**Escalation.** None normally; report repeated confusion as feedback for the maintainers.

### 11.10 "I can't share my calendar" or "How do I invite people or accept an invitation?"

**Symptom.** No sharing, attendee or RSVP control in the calendar.

**Likely causes, in order.**

1. The interface has no control for sharing a calendar, inviting attendees or answering an
   invitation; these exist only in the API (section 2.4).
2. Sharing with **everyone** additionally needs the `sharing.public_calendars` permission (off by
   default), and a grant the person may not give is silently dropped (section 3.1).

**Diagnostic steps.** None needed beyond confirming what the person is trying to do.

**Resolution.** Explain that calendar sharing and invitations are not available on screen in this
version. Whether MedIT GPT supports API use for this is **TO BE CONFIRMED**.

**Escalation.** Forward feature requests to the maintainers.

### 11.11 "I can't delete a calendar"

**Symptom.** No bin beside a calendar, or deleting fails.

**Likely causes, in order.**

1. It is the **default** calendar (normally `Personal`) or **Scheduled Tasks**; these cannot be
   deleted and show no bin.
2. It is someone else's calendar shared with the person: `Only owner can delete calendar` or
   `Access denied`.
3. On a narrow screen the calendar list (with the bin) is hidden; use a wider window.

**Diagnostic steps.** Ask which calendar and the exact message.

**Resolution.** Explain; the person can hide a calendar for the visit by clicking its name.

**Escalation.** `Failed to delete calendar` or `Failed to delete` repeatedly: send the time and
account to the maintainer (server log `Failed to delete calendar {id}: {e}`).

### 11.12 "The automation's answer has the wrong date"

**Symptom.** A prompt using `{{CURRENT_DATE}}`, `{{CURRENT_TIME}}` or `{{CURRENT_WEEKDAY}}` got a
date or time that is off, typically around midnight.

**Likely causes, in order.**

1. These variables are filled in with the **server's** clock and time zone, not the person's
   (`backend/open_webui/utils/task.py:84-94`).
2. Variables that only the chat page fills in, such as `{{CURRENT_TIMEZONE}}`, are left as typed
   in automation prompts, because runs use the server's template function
   (`src/lib/utils/index.ts:1228`; `backend/open_webui/utils/task.py:36-104`).

**Diagnostic steps.** Ask for the scheduled time and the date shown in the answer.

**Resolution.** Suggest writing the date reference into the instructions in words ("today in
Toronto time") or scheduling away from midnight.

**Escalation.** The server's time zone is deployment data (**TO BE CONFIRMED**); report if
widespread.

### 11.13 "Last run says Never, but it ran"

**Symptom.** **Last run** shows **Never** or an older time although **Runs** lists a newer run.

**Likely causes, in order.** **Last run** records only runs the scheduler started; **Run now** adds
to **Runs** without changing **Last run** (section 4.1).

**Diagnostic steps.** Ask whether the newer run came from **Run now**.

**Resolution.** Explain; **Runs** is the complete history.

**Escalation.** None.

### 11.14 "The reminder in my chat never went off" (Timer)

**Symptom.** The model said it set a timer, but nothing came back into the chat.

**Likely causes, in order.** See `builtin-native-tools.md` section 11.12 for the tool-side causes
(cancel options such as `chat.read`, the time given in UTC, sub-agents switched off). In addition,
from the scheduling side:

1. The server restarted while the timer was firing; such a timer stays `running` and is not
   retried (section 5.14).
2. The chat was busy with a reply at the due time; the timer waits until the chat is idle and then
   fires (section 5.14).
3. The parent chat was deleted; its timers are deleted with it.

**Diagnostic steps.** Ask for the chat name, when the timer was set and for what time, and whether
the chat was opened or written in before then.

**Resolution.** Ask the model to set the timer again, or use a calendar event or an automation for
anything important.

**Escalation.** Chat name, account, expected time; the maintainer can check the hidden timer
chat's status for that chat (data, not visible in the interface).

### 11.15 "My event is on the wrong day" or "It spans two days"

**Symptom.** An event shows across two days, has no length, or sits an hour or more away from the
time typed.

**Likely causes, in order.**

1. The form has no end-date field; changing the start date leaves the end on the original date, so
   the event can stretch over several days, or be cut to zero length when the end would fall before
   the start (section 5.11).
2. The browser's time zone differs from the one the person thinks they are in; times are read and
   shown in the browser's zone.
3. Repeating events are laid out in the person's **stored** time zone, so a mismatch with the
   browser's zone can shift occurrences, notably around daylight-saving changes
   (`backend/open_webui/routers/calendar.py:186-191`; `backend/open_webui/utils/calendar.py:36-42`).

**Diagnostic steps.** Ask for the date and times entered and a screenshot of the event form.

**Resolution.** Ask the person to delete the event and create it again from the right day (click
the day in month view, which pre-fills that date for start and end).

**Escalation.** None normally; persistent shifts for repeating events go to the maintainer with
the account (stored time zone is data).

## 12. Local Customisations

The automation, calendar and timer code **matches upstream Open WebUI v0.11.4**. A read-only
`git diff main...uoft` and `git diff` (working tree) over every file in scope report no changes:
the three routers and models, `utils/automations.py`, `utils/recurrence.py`, `utils/timers.py`,
`utils/calendar.py`, the three migrations, `constants.py`, `events.py`, `config.py` and `env.py`
lines in scope, `src/lib/components/automations/`, `src/lib/components/AutomationModal.svelte`,
`src/lib/components/calendar/`, `src/routes/(app)/automations/`, `src/routes/(app)/calendar/` and
`src/lib/apis/automations/` and `src/lib/apis/calendar/`. The uncommitted `en-US` translation change
does not touch any string used here.

Fork changes that are visible from this area:

| Change | Effect here | Source |
|---|---|---|
| Browser notification titles use the site name instead of the fixed text `Open WebUI` | Reminder and background-reply notifications read `{title} / {WEBUI_NAME}`, which is `MedIT GPT` by default (the live name is an environment value, TO BE CONFIRMED) | `git diff main...uoft -- src/routes/+layout.svelte` (hunks at lines 619 and 757); `src/routes/+layout.svelte:622`, `:760`; `backend/open_webui/env.py:951` |
| U of T favicon in `static/favicon.png` | The icon shown on those browser notifications | `src/routes/+layout.svelte:627`, `:765`; `ground-truth.md` (Fork changes) |
| Test notification text uses the site name | Not used by reminders, but a person testing a notification target before relying on it for **Calendar alert** sees `This is a test notification from {app_name}.` | `backend/open_webui/utils/notifications.py:349-366` |
| Browser tab titles `Automations / {WEBUI_NAME}` and `Calendar / {WEBUI_NAME}` | Already used the site name upstream; show `MedIT GPT` by default | `src/routes/(app)/automations/+page.svelte:411`; `src/routes/(app)/calendar/+page.svelte:212` |

No U of T-specific schedule, calendar (academic or business), time zone or limit is configured in
the repository; the server's time zone and the live switch and limit values are deployment data
(**TO BE CONFIRMED**).

## 13. Source File Index

### 13.1 Back End (In Scope, Read in Full)

| File | Lines | What it holds |
|---|---|---|
| `backend/open_webui/routers/automations.py` | 400 | Automation API: gates, ownership, folder and channel checks, limits, create, read, update, toggle, run now, delete, runs |
| `backend/open_webui/models/automations.py` | 460 | `automation` and `automation_run` tables, forms, search, claim of due automations, run history queries |
| `backend/open_webui/utils/automations.py` | 625 | The `scheduler_worker_loop`, run execution for chats and channels, model defaults for runs, calendar reminders, run recording, poll settings |
| `backend/open_webui/utils/recurrence.py` | 171 | Rule parsing, time-zone resolution, validation, next run times, interval measurement, 2-second evaluation limit |
| `backend/open_webui/utils/timers.py` | 429 | Timer creation, claim, cancellation, firing and failure states |
| `backend/open_webui/routers/calendar.py` | 485 | Calendar API, the Scheduled Tasks virtual calendar, events, RSVP, sharing checks |
| `backend/open_webui/models/calendar.py` | 862 | `calendar`, `calendar_event`, `calendar_event_attendee` tables, the `Personal` default, visibility, reminders query, daily recurrence minimum |
| `backend/open_webui/utils/calendar.py` | 86 | Expansion of recurring events into occurrences |
| `backend/open_webui/migrations/versions/d4e5f6a7b8c9_add_automation_tables.py` | — | Creates `automation` and `automation_run` |
| `backend/open_webui/migrations/versions/959eaac8f909_add_automation_folder_id.py` | — | Adds `automation.folder_id` |
| `backend/open_webui/migrations/versions/56359461a091_add_calendar_tables.py` | — | Creates the three calendar tables |

### 13.2 Back End (Read in Part, for This Area)

| File | What was used |
|---|---|
| `backend/open_webui/config.py` | Permission defaults (`:1837-1839`, `:1928-1930`, `:1972`, `:2013-2014`), switches and limits (`:2028-2048`), `DEFAULT_CONFIG` keys (`:3104-3117`) |
| `backend/open_webui/constants.py` | `ERROR_MESSAGES` texts (`:16-23`, `:69`, `:78`, `:116-123`) |
| `backend/open_webui/main.py` | Router mounts (`:882-883`), scheduler start and stop (`:403-405`, `:494`), chat completion entry, model access, approval mode and task fan-out (`:1110-1161`, `:1254-1264`, `:1638-1645`, `:1686-1712`, `:1802-1881`), `/api/config` features (`:2357-2358`) |
| `backend/open_webui/routers/auths.py` | Admin configuration keys and save (`:104-133`, `:1227-1296`), time-zone update (`:348-374`) |
| `backend/open_webui/events.py` | Event definitions (`:567-623`), notification events (`:669-675`), sinks and `publish_event` (`:1034-1202`) |
| `backend/open_webui/utils/notifications.py` | Reminder webhook text and delivery (`:264-347`, `:393-419`) |
| `backend/open_webui/utils/models.py` | `check_model_access` (`:465-520`) |
| `backend/open_webui/utils/task.py` | Template variables in prompts (`:36-104`) |
| `backend/open_webui/models/chats.py` | `timer_at` column, internal-chat filtering, `insert_new_chat` (`:140-183`, `:536-560`, `:591-600`) |
| `backend/open_webui/routers/chats.py` | Deleting a chat deletes its timers (`:1575-1615`) |
| `backend/open_webui/routers/folders.py` | Folder deletion clears automation folders (`:690-735`) |
| `backend/open_webui/routers/channels.py` | Channel posting rules used by channel runs (`:1137-1160`) |
| `backend/open_webui/socket/main.py` | Event emitter room (`:1134-1160`), `chat.read` timer cancellation (`:615-638`) |
| `backend/open_webui/tasks.py` | Busy-chat check (`:190-196`, `:312-315`) |
| `backend/open_webui/tools/builtin.py` | The `timer` tool (`:1721-1754`) and calendar tool helpers (`:4096-4290`); covered in `builtin-native-tools.md` |
| `backend/open_webui/utils/middleware.py` | Chat finished and failed events (`:206-232`, `:4387-4405`) |
| `backend/open_webui/models/access_grants.py` | Calendar visibility filter (`:723-773`) |
| `backend/open_webui/models/users.py` | `timezone` column (`:160`), activity window (`:918-925`) |
| `backend/open_webui/migrations/versions/d4c1a8e37b62_add_chat_timer_at_and_chat_indexes.py` | Adds `chat.timer_at` |

### 13.3 Front End

| File | Lines | What it holds |
|---|---|---|
| `src/routes/(app)/automations/+layout.svelte` | 131 | Header, count, access redirect |
| `src/routes/(app)/automations/+page.svelte` | 737 | List, search, filter, bulk enable or disable, import, export, clone, run now, delete (including Shift-delete) |
| `src/routes/(app)/automations/[id]/+page.svelte` | 51 | Loads one automation into the editor |
| `src/lib/components/AutomationModal.svelte` | 224 | Create and edit form |
| `src/lib/components/automations/AutomationEditor.svelte` | 416 | Detail page: status, schedule, destination, next and last run, prompt, runs |
| `src/lib/components/automations/ScheduleDropdown.svelte` | 309 | Schedule picker and rule builder |
| `src/lib/components/automations/ModelDropdown.svelte` | 130 | Model picker |
| `src/lib/components/automations/DestinationDropdown.svelte` | 315 | New chat, folder or channel picker |
| `src/lib/components/automations/AutomationMenu.svelte` | 114 | Row menu (Edit, Clone, Run Now, Delete) |
| `src/lib/components/automations/AutomationItemHeaderActions.svelte` | 70 | Editor header (switch, Run now, Edit, Delete) |
| `src/lib/components/automations/AutomationListHeaderActions.svelte` | 9 | List header (Create, Import JSON, Export JSON) |
| `src/lib/components/automations/FolderDropdown.svelte` | 148 | Not used by any page in v0.11.4 |
| `src/lib/components/automations/TerminalDropdown.svelte` | 118 | Not used by any page in v0.11.4 |
| `src/routes/(app)/calendar/+page.svelte` | 380 | Calendar page, loading, navigation, delete calendar, event clicks |
| `src/lib/components/calendar/CalendarView.svelte` | 326 | Month, week and day grids |
| `src/lib/components/calendar/CalendarSidebar.svelte` | 252 | Mini month, calendar list, new and delete calendar |
| `src/lib/components/calendar/CalendarEventModal.svelte` | 352 | Event form, repeat and reminder choices, delete |
| `src/lib/components/calendar/CreateCalendarModal.svelte` | 148 | New calendar form |
| `src/lib/components/calendar/CalendarEventChip.svelte` | 32 | Event chip |
| `src/lib/apis/automations/index.ts` | 312 | Automation API client |
| `src/lib/apis/calendar/index.ts` | 458 | Calendar API client |
| `src/routes/+layout.svelte` | (part) | Reminder toast and notification (`:600-628`), background-reply toast (`:735-781`), time-zone sync (`:1293-1297`) |
| `src/lib/components/layout/Sidebar.svelte`, `src/lib/components/layout/Sidebar/UserMenu.svelte` | (part) | Menu entries and pinning |
| `src/lib/components/admin/Settings/General.svelte` | (part) | **Calendar** and **Automations** switches (`:365-378`) |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | (part) | Permission switches (`:518-536`, `:1114-1151`) |
| `src/lib/components/chat/Settings/Notifications.svelte` | (part) | Browser notifications and notification targets |
| `src/lib/components/chat/Messages/UserMessage.svelte` | (part) | Collapsed **Timer** row (`:346-377`) |
| `src/lib/components/common/ConfirmDialog.svelte` | (part) | Dialog defaults |
| `src/lib/i18n/locales/en-US/translation.json` | (part) | Dotted keys for the admin switches (`:2370-2374`), notification labels (`:2996-2999`), plural keys (`:905-908`, `:3128-3129`) |

## 14. Open Questions

### 14.1 Live Configuration (Data, Not Code): TO BE CONFIRMED

1. The live values of `automations.enable`, `calendar.enable`, `automations.max_count`,
   `automations.min_interval` and `automations.auth_token_expires_in` in the production `config`
   table (code defaults: on, on, no limit, no limit, `1h`).
2. The live default and group permissions `features.automations` (code default off),
   `features.calendar` (on) and `sharing.public_calendars` (off): in other words, whether MedIT GPT
   users are meant to have automations at all.
3. The related switches `channels.enable`, `ui.enable_user_webhooks`, `features.webhooks` and
   `subagents.enable` (all off in code), which decide channel destinations, reminder webhooks and
   whether the model can set timers.
4. The environment values of `SCHEDULER_POLL_INTERVAL` (or `AUTOMATION_POLL_INTERVAL`),
   `TIMER_POLL_INTERVAL` and `CALENDAR_ALERT_LOOKAHEAD_MINUTES` on the production host.
5. The production server's time zone: it is the fallback for people with no stored time zone and
   the source of `{{CURRENT_DATE}}`-style variables in automation prompts.
6. The number of server processes and replicas, and whether production uses SQLite or
   PostgreSQL and Redis (section 8.3; `ground-truth.md`, Environments). Several processes on
   SQLite would make the open questions in 14.3 items 1 and 2 relevant.
7. Whether an admin should set `automations.min_interval` (and `automations.max_count`) for
   MedIT GPT; with the code defaults a person can schedule a run every few seconds.
8. The live `WEBUI_NAME` shown in notification and tab titles (default `MedIT GPT`).

### 14.2 Organisational and Privacy Questions: TO BE CONFIRMED

1. Who decides whether automations and the calendar are offered to MedIT GPT users, and who
   handles access requests (no contact or route exists in the repository).
2. Whether people may use the API directly for what the interface lacks (calendar sharing,
   attendees, invitation answers); user API keys are off by default (`ground-truth.md`).
3. Retention: nothing deletes `automation_run` rows except deleting the automation, and every run
   leaves a new chat. Whether a retention rule applies to automation chats and run history.
4. Automations, calendars and events of **deleted users** remain, and the scheduler keeps
   recording `User not found` for their active automations at every scheduled time (section 6.7).
   Who cleans these up, and how, is not defined in the code.
5. Prompts, run chats, exported automation files, event titles, descriptions and locations, and
   event payloads sent to admin webhooks can contain personal or health information; the handling
   rules for support staff are not in the repository.
6. Whether tier 1 can see Admin Settings or the database (read-only) when diagnosing, or must
   always escalate (the procedures in section 11 assume they cannot).

### 14.3 Behaviour Read from Code, to Confirm in a Test Environment

1. **SQLite with several processes**: whether two processes can claim the same automation or the
   same timer at once. Row locks are used only on PostgreSQL
   (`backend/open_webui/models/automations.py:308-309`; `backend/open_webui/utils/timers.py:181-182`).
   The sibling `builtin-native-tools.md` (section 14) lists the same question for timers.
2. **Duplicate reminders** when several processes check at the same moment: reminders are not
   claimed before being sent (`backend/open_webui/utils/automations.py:552-592`).
3. **Seconds offset**: daily, weekly and monthly rules without `DTSTART` take the evaluation
   moment as their start, so runs fall at the chosen minute plus the seconds of that moment.
   Checked against the installed python-dateutil library with a scratch script, not in the app.
4. **Once default date** is the UTC date, so it is tomorrow's date in the evening in Toronto
   (`src/lib/components/automations/ScheduleDropdown.svelte:53-57`).
5. **Event end date**: the form has no end-date field, so changing the start date can stretch an
   event over several days or make it zero-length
   (`src/lib/components/calendar/CalendarEventModal.svelte:95-108`, `:131-137`).
6. **Recurring events** are edited and deleted only as whole series; editing from a later
   occurrence moves the series' start; a recurrence the form does not recognise is removed when the
   form is saved (section 5.11).
7. **Reminders**: sent once per event, only for a recurring event's first start, not re-armed by
   edits, and sent about an hour ahead when set further ahead through the API (section 5.13).
8. **First run after a restart**: the run reads the model's default tools, filters and features
   from the in-memory model list before the chat pipeline loads it, so the first run in a freshly
   started process may run without the model's default tools
   (`backend/open_webui/utils/automations.py:166-176`, `:474-475`; `backend/open_webui/main.py:1115-1116`).
9. **A calendar shared with everyone** in a new user's list prevents the automatic `Personal`
   calendar, and may become the form's pre-selected calendar
   (`backend/open_webui/models/calendar.py:291-312`; `src/routes/(app)/calendar/+page.svelte:194`).
10. **Timers interrupted by a restart** stay `running` and never fire (section 5.14).
11. **Timers without Redis** may fire into a chat that another process is still answering
    (section 8.3).
12. **A non-integer** `SCHEDULER_POLL_INTERVAL`, `TIMER_POLL_INTERVAL` or
    `CALENDAR_ALERT_LOOKAHEAD_MINUTES` stops the application from starting, because the values are
    converted when the module loads (`backend/open_webui/utils/automations.py:53-55`).
13. **Evaluation timeouts after validation**: on create and update the rule is evaluated again
    after it has been validated (`backend/open_webui/routers/automations.py:226-229`, `:286-289`);
    a timeout at that later point is not turned into a readable message, so the person would see a
    generic server error. Not established.
14. **Scheduled Tasks for very frequent automations**: at most 5,000 upcoming entries are computed
    per automation per view, so a five-minute automation fills only part of a month view
    (`backend/open_webui/utils/calendar.py:22`, `:61`).
15. **Import of a file with the wrong shape** (an object without an `automations` list) reports
    `Imported automations successfully` and creates nothing
    (`src/routes/(app)/automations/+page.svelte:282-308`, `:436-438`).
16. **Daylight-saving behaviour** of schedules for people with no stored time zone on a server that
    does not follow Toronto time (section 11.3).
17. **Monthly on the 29th to 31st** skipping short months and `Z` or `TZID` in a custom `DTSTART`
    being read in the person's zone: checked against the installed python-dateutil library and the
    code path, not in the running app (`backend/open_webui/utils/recurrence.py:46-66`).

### 14.4 Discrepancies Noticed in the Code (No Contradiction with Ground Truth)

1. The module description of `backend/open_webui/utils/automations.py` gives the default reminder
   lead time as 5 minutes (`:15`); the code uses 10 (`:55`).
2. `claim_due`'s comment says a row "can never be double-claimed"; only PostgreSQL takes row locks
   (`backend/open_webui/models/automations.py:290-296`, `:308-309`).
3. `_check_calendar_alerts`' comment says de-duplication "works across multiple instances"; there
   is no claim step (`backend/open_webui/utils/automations.py:537-542`).
4. The generated `tools/inventory.md` lists `automation_worker_loop` among "background loops
   started at startup"; it is only an alias and is never started
   (`backend/open_webui/utils/automations.py:63-66`; `backend/open_webui/main.py:403-405`).
5. The index `ix_automation_run_aid_created` is declared in the model but created by no migration
   (`backend/open_webui/models/automations.py:52-55`; section 6.2).
6. `data.terminal`, the `_set_terminal_cwd` helper and the `FolderDropdown` and `TerminalDropdown`
   components exist but are not used in v0.11.4 (section 6.1).
7. The server sends `automation:result` to the browser, but no front-end code listens for it
   (section 9.1).
8. A run is recorded as `success` when the reply starts, although the function's description says
   the automation is executed "through the full chat completion pipeline"
   (`backend/open_webui/utils/automations.py:345-351`, `:494-511`).
9. The Automations pages check access in the browser and redirect; the Calendar page does not
   (section 2.1).
10. The calendar list shows a delete bin on calendars that other people own and share, which the
    server then refuses (section 5.12).
11. `get_admin_user` is imported by the automations router but no route uses it
    (`backend/open_webui/routers/automations.py:23`).
12. The admin configuration API accepts `AUTOMATION_MAX_COUNT` and `AUTOMATION_MIN_INTERVAL`, but
    no settings screen has a field for them (`backend/open_webui/routers/auths.py:1227-1228`;
    no use in `src/`).
13. The model-editor description of the **Calendar** tool group mentions listing calendars, which
    no tool does (already noted in `builtin-native-tools.md` section 10.2).

### 14.5 Security-Sensitive Questions

1. How automation runs act as their owner towards tool servers and terminals
   (`automations.auth_token_expires_in`). Security-sensitive: refer to the platform maintainer and
   U of T Information Security (security.utoronto.ca).
2. Calendar invitation handling through the API (who may be added as an attendee, and what then
   appears in their calendar). Security-sensitive: refer to the platform maintainer and U of T
   Information Security (security.utoronto.ca).
