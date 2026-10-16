# Channels and Direct Messages

## At a Glance

- Channels are group chat spaces between people inside MedIT GPT; a model can join the
  conversation when someone mentions it with `@`. Provisional: refined at the end.
- Channels are switched off by default (`channels.enable`), and a non-admin also needs the
  `features.channels` permission. Provisional: refined at the end.
- Channel types cover public and private channels, groups and direct messages; membership,
  manager roles, threads, reactions, pins, files and webhooks are covered below.
  Provisional: refined at the end.

*Refined 2026-10-10, once sections 1 to 14 were complete:*

- **Off unless an admin turns it on.** The site switch `channels.enable` is off by default; when
  it is on, the `features.channels` permission is on by default for everyone (sections 3.1, 7.1).
- **Three kinds.** Standard channels (admins create them; access lists decide who reads and
  writes), group channels (members only; "Public" changes only the icon) and direct messages
  (participants only; from the screens they can be hidden, not left or deleted) (sections 1, 4, 5).
- **Models answer only when picked from the `@` list** (or when someone uses **Reply** on a model's
  message), only if the poster can use that model, and by default in a thread under the message
  (sections 3.5, 5.6, 11.3).
- **Nobody is told when they are added** to a group channel; they reload to see it (sections 5.3,
  11.2).
- **Deleting has no undo.** A deleted message or channel cannot be brought back from the screens,
  yet a deleted channel's messages stay in the database, unreachable (sections 5.7, 5.8).
- **No email.** Pop-ups and browser notifications need the page open; notification targets work
  only for standard channels (section 9).
- **Webhook addresses are secrets**: never put one in a ticket (sections 5.9, 11.6).
- **Most refusals read `Something went wrong :/`**, and some failures show nothing at all
  (section 10).
- **Fork changes are small**: the tab title uses the app name, and **Hide Processing Details** also
  applies to model replies in channels (section 12).

## 1. Purpose and Who Uses It

Channels are MedIT GPT's built-in group messaging. People post short messages to each other in a
shared space, reply in threads, react with emoji, pin important messages and attach files. A
channel is not a chat with a model: a model only takes part when someone mentions it with `@` (or
replies to a message the model wrote), and it then answers inside the channel using the full chat
pipeline (`backend/open_webui/routers/channels.py:976-1134`).

There are three kinds of channel, plus direct messages (detail in sections 4 and 5):

| Kind (code value) | Shown in the create dialog as | Who can create it | Who can see it | Source |
|---|---|---|---|---|
| Standard channel (type empty) | **Channel** | Admins only | Whoever its access list grants read to (everyone when it is **Public**); admins can open every standard channel | `backend/open_webui/routers/channels.py:305-310`, `:433-435`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:77-82`, `:194-196` |
| Group channel (`group`) | **Group Channel** | Anyone with the Channels feature | Members only | `backend/open_webui/routers/channels.py:305`, `:399-401`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:190-191` |
| Direct message (`dm`) | **Direct Message** | Anyone with the Channels feature | The people in the conversation only | `src/lib/components/layout/Sidebar/ChannelModal.svelte:192-193`; `backend/open_webui/models/channels.py:398-409` |

Who uses this area:

| Person | What they do here | Source |
|---|---|---|
| Any signed-in user (role `user`) with the `features.channels` permission | Opens channels they can see, posts, replies, reacts, pins (with write access), starts group channels and direct messages, mentions models | `backend/open_webui/routers/channels.py:141-156`, `:305-310` |
| Channel creator | Renames the channel, changes visibility or access, adds and removes group members, deletes the channel, manages incoming webhooks | `backend/open_webui/routers/channels.py:641`, `:685`, `:723`, `:767`, `:1890`, `:1910`, `:1942`, `:1977` |
| Admin | Turns the whole feature on or off, sets the model reply placement, grants or withholds the permission per group, creates standard channels, and can manage or delete any channel through the API | `backend/open_webui/routers/auths.py:125-126`; `src/lib/components/admin/Settings/General.svelte:342-363` |
| Outside system (through a webhook URL) | Posts messages into one channel without signing in, as a named "webhook" sender | `backend/open_webui/routers/channels.py:2005-2084` |
| Tier-1 support | Explains why Channels are missing, why a model did not answer, why a message or channel is gone, and why notifications do not arrive; escalates anything that needs a setting or access change | sections 10 and 11 |

Channels are **off by default**: the site-wide switch `channels.enable` is seeded from
`ENABLE_CHANNELS`, whose code default is `False` (`backend/open_webui/config.py:2028`, `:3104`).
Whether production has switched it on is data in the `config` table: **TO BE CONFIRMED**. When it
is off, the sidebar shows no Channels section and every channel endpoint refuses with
`Channels is disabled` (`backend/open_webui/routers/channels.py:143-147`;
`src/lib/components/layout/Sidebar.svelte:1330`).

Channel content may include personal or health information typed by users. It is stored in the
relational database (tables in section 6), it can be read by models when they are mentioned or
when the channel tools are used (`builtin-native-tools.md`), and admins can open any standard
channel (section 3.4). Treat channel content as personal data.

## 2. Navigation and URLs

The host name of production is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Screens and Controls

| Place | Path or how to reach it | Who sees it | What it holds | Source |
|---|---|---|---|---|
| Sidebar **Channels** section | Left sidebar, between pinned notes and folders; the **+** button has the label **Create Channel** | Shown only when `channels.enable` is on and the person is an admin or has `features.channels` | Every channel, group channel and direct message the person can see, sorted standard first, then group channels, then direct messages, with a divider between kinds | `src/lib/components/layout/Sidebar.svelte:1330-1361`, `:360-373` |
| Channel row | One line per channel in that section | As above | `#` icon for a public channel, padlock for a private one; for a direct message, up to two profile pictures and a green dot when the other person is active; a small count with the label **Unread** when there are unread messages | `src/lib/components/layout/Sidebar/ChannelItem.svelte:113-201` |
| Channel row gear button | Hover a standard or group channel row | Admins and the channel's creator | Opens **Edit Channel** | `src/lib/components/layout/Sidebar/ChannelItem.svelte:230-243` |
| Direct message row **×** button | Hover a direct message row | Every participant | Hides that direct message from the person's sidebar (it is not deleted; section 5.4) | `src/lib/components/layout/Sidebar/ChannelItem.svelte:205-229` |
| **Create Channel** dialog | Sidebar **Channels** › **+** | As for the section | **Channel Type** (admins: **Channel**, **Group Channel**, **Direct Message**; others: **Group Channel**, **Direct Message**), **Channel Name**, then the access panel (**Private** or **Public**, **Allow public write access**, **Access List**) for a standard channel, **Visibility** for a group channel, or a people picker for a direct message | `src/lib/components/layout/Sidebar/ChannelModal.svelte:141-260`, `:77-82` |
| **Edit Channel** dialog | Channel row gear button | Admins and the creator | Name, visibility or access, **Webhooks** › **Manage**, **Delete**, **Update** | `src/lib/components/layout/Sidebar/ChannelModal.svelte:145-147`, `:262-309` |
| Channel page | `/channels/{id}` | Anyone allowed to read that channel | The message list (newest at the bottom, 50 at a time, older ones load on scroll), the message box, and a top bar | `src/routes/(app)/channels/[id]/+page.svelte:7`; `src/lib/components/channel/Channel.svelte:124-141`, `:355-417` |
| Thread link | `/channels/{id}?thread={message id}` | As above | Opens the channel with that message's thread panel open; the browser address then drops `?thread=` | `src/lib/components/channel/Channel.svelte:53-56` |
| Thread panel | A message's **Reply in Thread** button, or its "{n} Replies" line | As above | Titled **Thread**; a resizable side panel (320 to 640 px) on screens at least 1,024 px wide, a drawer on smaller screens | `src/lib/components/channel/Channel.svelte:427-466`; `src/lib/components/channel/Thread.svelte:186-187` |
| **Pinned Messages** button | Channel top bar, pin icon | Everyone in the channel | Opens the **Pinned Messages** list, newest pin first, 20 at a time | `src/lib/components/channel/Navbar.svelte:159-172`; `src/lib/components/channel/PinnedMessagesModal.svelte:69-161`; `backend/open_webui/routers/channels.py:868` |
| Member count button | Channel top bar, person icon with a number (tooltip **Users**) | Everyone in the channel | Opens the channel information window with the member list; for a group channel's creator also **Add** and remove buttons | `src/lib/components/channel/Navbar.svelte:174-193`; `src/lib/components/channel/ChannelInfoModal.svelte:71-137` |
| Message toolbar | Hover a message (swipe right on a touch screen to reply) | People with write access; buttons hidden otherwise | **Add Reaction**, **Reply**, **Pin** or **Unpin**, **Reply in Thread**, and for the author or an admin **Edit** and **Delete** | `src/lib/components/channel/Messages/Message.svelte:210-305`, `:89-138`; `src/lib/components/channel/Messages.svelte:134` |
| Profile preview **Message** button | Click a person's picture in a channel, in a member list or on a mention | Anyone, for someone other than themselves | Opens (or creates) a direct message with that person | `src/lib/components/channel/Messages/Message/UserStatus.svelte:19-32`, `:117-137` |
| Admin switch | **Admin Settings › General › Features › Channels**; `/admin/settings/general` (opens `/?settings=admin:general`) | Admins | The site-wide `channels.enable` switch and, when it is on, **Model Response Mode** | `src/lib/components/admin/Settings/General.svelte:274`, `:342-363`; `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10` |
| Permission switch | **Admin Panel › Users › Groups**, a group or **Default permissions**, **Features Permissions** › **Channels**; `/admin/users/groups` | Admins | The `features.channels` permission | `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:994-1008` |
| Browser notifications | **Settings › Notifications › Browser Notifications**; `/?settings=notifications` | Every user | Whether channel messages (and finished chat replies) raise a browser notification | `src/lib/components/chat/Settings/Notifications.svelte:193-210`; `src/lib/components/chat/SettingsModal.svelte:200-203`; `src/routes/(app)/+layout.svelte:165-193` |

When a channel cannot be opened (it was deleted, the person lost access, or Channels are off), the
channel page sends the person to the home page `/` without any message
(`src/lib/components/channel/Channel.svelte:124-140`). The same happens in the thread panel when the
channel is missing (`src/lib/components/channel/Thread.svelte:51-62`).

The English labels of the dotted keys used above are in
`src/lib/i18n/locales/en-US/translation.json`: **Channels** and its description "Allow users to use
channels for shared conversations." (`:2375-2376`), **Model Response Mode** and "Choose where model
responses to root-level channel mentions are posted." (`:2396-2397`), the section title
**Features** (`:2402`), **General** (`:2405`), **Notifications** and **Browser Notifications**
(`:2996`, `:2999`).

### 2.2 API Endpoints

The router is mounted at `/api/v1/channels` (`backend/open_webui/main.py:860`). Every endpoint
first checks the site switch and, for signed-in callers, the permission (section 3.1).

| Method and path | What it does | Who may call it | Source |
|---|---|---|---|
| `GET /api/v1/channels/` | Sidebar list with unread counts and, for direct messages, the participants | Signed-in users | `backend/open_webui/routers/channels.py:172-218` |
| `GET /api/v1/channels/list` | Every channel (admins) or the person's own list | Signed-in users | `:221-230` |
| `GET /api/v1/channels/users/{user_id}` | Find or create the direct message with one person | Signed-in users | `:238-288` |
| `POST /api/v1/channels/create` | Create a channel, group channel or direct message | Signed-in users; standard channels admins only | `:296-368` |
| `GET /api/v1/channels/{id}` | One channel with members, manager flag, write access, unread count | Readers | `:384-476` |
| `GET /api/v1/channels/{id}/members` | Member list, 30 per page, searchable | Readers | `:513-578` |
| `POST /api/v1/channels/{id}/members/active` | Show or hide the channel in the caller's own list | Members | `:591-615` |
| `POST /api/v1/channels/{id}/update/members/add` and `/remove` | Add or remove members | Creator or admin | `:628-701` |
| `POST /api/v1/channels/{id}/update` | Rename, change visibility, access or details | Creator or admin | `:709-746` |
| `DELETE /api/v1/channels/{id}/delete` | Delete the channel | Creator or admin | `:754-788` |
| `GET /api/v1/channels/{id}/messages` | Top-level messages, 50 per page | Readers | `:803-863` |
| `GET /api/v1/channels/{id}/messages/pinned` | Pinned messages, 20 per page | Readers | `:871-933` |
| `POST /api/v1/channels/{id}/messages/post` | Post a message (and trigger model replies and notifications) | Writers | `:1216-1270` |
| `GET /api/v1/channels/{id}/messages/{message_id}` and `/data` | One message, or its attachments and output | Readers | `:1278-1346` |
| `POST /api/v1/channels/{id}/messages/{message_id}/pin` | Pin or unpin | Members (group, direct message) or writers (standard) | `:1358-1424` |
| `GET /api/v1/channels/{id}/messages/{message_id}/thread` | Thread replies, 50 per page | Readers | `:1432-1486` |
| `POST /api/v1/channels/{id}/messages/{message_id}/update` | Edit a message | Its author or an admin | `:1494-1560` |
| `POST /api/v1/channels/{id}/messages/{message_id}/reactions/add` and `/remove` | Add or remove the caller's reaction | Writers | `:1572-1713` |
| `DELETE /api/v1/channels/{id}/messages/{message_id}/delete` | Delete a message | Its author or an admin | `:1721-1810` |
| `GET`, `POST …/create`, `POST …/{webhook_id}/update`, `DELETE …/{webhook_id}/delete` under `/api/v1/channels/{id}/webhooks` | List, create, rename or delete incoming webhooks | Creator (manager) or admin | `:1877-1994` |
| `GET /api/v1/channels/webhooks/{webhook_id}/profile/image` | A webhook's picture | Readers | `:1818-1874` |
| Incoming webhook URL | Posts a message from an outside system; the URL itself is the credential (section 5.9) | Whoever holds the URL | `:2005-2084` |

"Readers" and "writers" mean: for a group channel or direct message, an active member; for a
standard channel, someone whose access grants include read (or write), or an admin
(section 3.2).

## 3. Roles and Permissions

### 3.1 The Site Switch and the Feature Permission

Two gates sit in front of everything in this area. Both are checked by the server on every channel
endpoint (`check_channels_access`, `backend/open_webui/routers/channels.py:141-156`).

| Gate | Key and environment variable | Code default | When it says no | Source |
|---|---|---|---|---|
| Site switch | `channels.enable`; `ENABLE_CHANNELS` | **Off** | Every endpoint answers HTTP 403 `Channels is disabled`, including incoming webhooks; the sidebar section is hidden for everyone, admins included | `backend/open_webui/config.py:2028`, `:3104`; `backend/open_webui/routers/channels.py:143-147`, `:2014`; `src/lib/components/layout/Sidebar.svelte:1330` |
| Feature permission | `features.channels` in `user.permissions`; `USER_PERMISSIONS_FEATURES_CHANNELS` | **On** | A non-admin gets HTTP 401 `401 Unauthorized`; the sidebar section is hidden; the live-update room check reads the permission from the person's groups and the environment default only, not from the saved **Default permissions** *(Corrected 2026-10-10: the first version said the person's browser connection is not added to any channel's live-update room; that holds only when no group grants the permission and the environment default `USER_PERMISSIONS_FEATURES_CHANNELS` is off, because the room check passes no saved defaults to `has_permission`, `backend/open_webui/utils/access_control/__init__.py:75-108`. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).)* | `backend/open_webui/config.py:1922`, `:2006`; `backend/open_webui/routers/channels.py:149-156`; `src/lib/components/layout/Sidebar.svelte:406-411`, `:1330`; `backend/open_webui/socket/main.py:479-484`, `:511-516` |

- Admins skip the feature permission but not the site switch
  (`backend/open_webui/routers/channels.py:143-150`).
- Permissions add up across groups (ground truth): a group cannot take away a permission the
  defaults grant. The group editor says so under the switch:
  `This is a default user permission and will remain enabled.`
  (`src/lib/components/admin/Users/Groups/Permissions.svelte:1001-1007`).
  To limit Channels to some people, the default must be off and the permission granted to chosen
  groups.
- The front end treats a missing `features.channels` value as on (`?? true`,
  `src/lib/components/layout/Sidebar.svelte:409`); the server reads the stored value.
- The socket room check looks only at the permission, not at the site switch
  (`backend/open_webui/socket/main.py:480`, `:512`); with the switch off nothing can be posted, so
  nothing is sent to those rooms.
- `sharing.public_channels` is checked when a channel is created or saved, but it is not in the
  default permissions or the group editor, so for non-admins any public (everyone) grant is removed
  on save (`backend/open_webui/routers/channels.py:312-318`, `:726-732`;
  `backend/open_webui/utils/access_control/__init__.py:256-274`; already recorded in
  `users-groups-roles-and-permissions.md`). Individual-person and group grants are likewise removed
  when the saver lacks `access_grants.allow_users` or `access_grants.allow_groups`
  (`backend/open_webui/utils/access_control/__init__.py:276-299`). In practice this matters only for
  standard channels, which only admins create.

### 3.2 What Each Person Can Do, by Channel Kind

"Member" means an **active** row in `channel_member` (`is_active` true,
`backend/open_webui/models/channels.py:675-686`). "Read grant" and "write grant" mean an access
grant on the channel for everyone (`user:*`), for the person, or for one of their groups
(`backend/open_webui/models/access_grants.py:562-618`).

| Action | Standard channel | Group channel | Direct message | Source |
|---|---|---|---|---|
| Create | Admins only | Anyone past the gates | Anyone past the gates | `backend/open_webui/routers/channels.py:305-310` |
| See it in the sidebar | Creator, or a read grant | Active member | Active member | `backend/open_webui/models/channels.py:394-430` |
| Open it and read messages, threads, pins, members | Read grant, or admin | Active member (no admin exception) | Active member (no admin exception) | `backend/open_webui/routers/channels.py:399-401`, `:433-435`, `:817-822` |
| Post, reply, react | Write grant (including public write), or admin | Active member | Active member | `backend/open_webui/routers/channels.py:1142-1153`, `:1586-1597` |
| Pin or unpin any message | Write grant, or admin | Active member | Active member | `backend/open_webui/routers/channels.py:1372-1378` |
| Edit or delete a message | The message's author (with write access), or admin | The author (an active member), or an admin who is a member | As group | `backend/open_webui/routers/channels.py:1515-1528`, `:1741-1758` |
| Rename, change visibility or access, delete the channel | Creator or admin | Creator or admin | Creator or admin (no button for direct messages) | `backend/open_webui/routers/channels.py:723`, `:767`; `src/lib/components/layout/Sidebar/ChannelItem.svelte:205-243` |
| Add or remove members | Creator or admin (server); no button | Creator (server: creator or admin; button: creator only) | Creator or admin (server); no button | `backend/open_webui/routers/channels.py:641`, `:685`; `src/lib/components/channel/ChannelInfoModal.svelte:119-128` |
| Manage incoming webhooks | Manager or admin | Manager or admin | Manager or admin | `backend/open_webui/routers/channels.py:1890`, `:1910`, `:1942`, `:1977` |
| Hide it from one's own sidebar | No button | No button | Any participant (**×**) | `src/lib/components/layout/Sidebar/ChannelItem.svelte:205-229`; `backend/open_webui/routers/channels.py:591-615` |

Points that surprise people:

- In group channels and direct messages every active member has write access; the server sends
  `write_access` true for them (`backend/open_webui/routers/channels.py:427`). In a standard channel
  a person can have read without write; the message box is then disabled, showing
  `You do not have permission to send messages in this channel.`, and the message toolbar is hidden
  (`src/lib/components/channel/Channel.svelte:408-411`;
  `src/lib/components/channel/Messages.svelte:134`).
- The **Edit** and **Delete** buttons appear for the message's author and for admins
  (`src/lib/components/channel/Messages/Message.svelte:277-302`). A model's reply is stored under
  the person who mentioned the model (section 5.6), so that person can also edit or delete it.
- There is **no "leave channel" action**. The data layer has one, but no endpoint calls it
  (`backend/open_webui/models/channels.py:566-584`; a search of `backend/open_webui` found no
  caller). Group members can only be removed by the creator; direct message participants can only
  hide the conversation.

### 3.3 The "Manager" Role

The server treats a person as a channel **manager** when they created the channel or when their
membership row has the role `manager` and is active
(`backend/open_webui/models/channels.py:510-526`). No code in this version sets the `manager` role:
new memberships are created without a role (`backend/open_webui/models/channels.py:297-325`,
`:528-564`), and a search of `backend/open_webui` and `src/lib` for the role value found it only in
that check. In practice **the creator is the only manager**. The flag reaches the browser as
`is_manager` (`backend/open_webui/routers/channels.py:426`, `:463`) and controls the **Add Member**
and remove buttons of a group channel's member list
(`src/lib/components/channel/ChannelInfoModal.svelte:119-128`). An admin who did not create a
group channel therefore does not see those buttons, although the server would accept the change.

### 3.4 What Admins Can See (Privacy)

| Content | Can an admin open it? | Source |
|---|---|---|
| Messages in any standard channel | Yes, whatever the access list says, and the admin can post, pin, edit and delete there | `backend/open_webui/routers/channels.py:433-435`, `:1146`, `:1377`, `:1522-1528`, `:1748-1758` |
| Standard channels in the sidebar | Only those the admin created or holds a grant for; other standard channels open only by link | `backend/open_webui/models/channels.py:411-420`; `backend/open_webui/models/access_grants.py:723-800` |
| The list of every channel, including group channels and direct messages | Yes, through `GET /api/v1/channels/list` (no screen in this version calls it) | `backend/open_webui/routers/channels.py:221-230`; a search of `src` for the path found no caller |
| Messages in a group channel or direct message the admin is not in | No: these endpoints require active membership and have no admin exception | `backend/open_webui/routers/channels.py:399-401`, `:817-819`, `:1291-1293` |
| Membership, name, visibility and deletion of any channel | Yes, through the server (the screens show these controls only to the creator) | `backend/open_webui/routers/channels.py:641`, `:685`, `:723`, `:767` |

Anyone with access to the database (or to backups of it) can read every channel message regardless
of these rules (tables in section 6). Whether admins may read or change private conversations, and
how such access is recorded, is a policy question: **TO BE CONFIRMED** with the Privacy Office
(privacy.utoronto.ca).

Personal data visible to members: the member list shows each member's name, role and, on hover,
email address (`src/lib/components/channel/ChannelInfoModal/UserList.svelte:217-256`;
`backend/open_webui/routers/channels.py:480-510`). For a public standard channel the "members" are
every user who is not pending (`backend/open_webui/routers/channels.py:555-563`). This matches the
ground-truth fact that any signed-in user can look up other users.

### 3.5 Model Access in Channels

- The models a person can mention are the models in their own model list, excluding their own
  direct connections (`src/lib/components/channel/MessageInput/MentionList.svelte:153-158`).
- When a message is posted, the server rebuilds the poster's filtered model list and answers only
  for mentioned models in it (`backend/open_webui/routers/channels.py:977`, `:1001-1005`). Model
  access control therefore applies to **the person who mentioned the model**, not to the other
  members. A mention of a model the poster cannot use is silently ignored (section 11.3).
- The reply goes through the normal chat completion endpoint as the poster, which re-checks
  channel membership or write access and that the reply message belongs to the poster
  (`backend/open_webui/main.py:1309-1350`).
- Tools in channel replies always run with **Full access**, whatever the person's approval choice
  (`backend/open_webui/main.py:1255-1263`; see `builtin-native-tools.md`).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| Channel (standard channel) | A channel whose `type` is empty. Access comes from access grants (read and write) on the channel, set in the access panel: **Private** (only the people and groups listed), **Public** (everyone who is not pending can read) and **Allow public write access** (everyone can also post). Only admins can create one | `backend/open_webui/routers/channels.py:305-310`, `:433-443`; `src/lib/components/workspace/common/AccessControl.svelte:517-560` |
| Group channel | `type` `group`. Access is membership only: a person sees and uses it only while they have an active membership row | `backend/open_webui/models/channels.py:398-409`; `backend/open_webui/routers/channels.py:399-401` |
| Group channel **Visibility** | **Public** ("Visible to all users") or **Private** ("Only invited users can access"), stored as `is_private`. The server uses it for nothing but storing and returning it; it only changes the `#` or padlock icon. A "public" group channel is still invisible to non-members (section 11.2) | `src/lib/components/workspace/common/Visibility.svelte:41-50`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:240-251`; `backend/open_webui/models/channels.py:50-51`, `:841`; `src/lib/components/layout/Sidebar/ChannelItem.svelte:38-46` |
| Direct message (DM) | `type` `dm`: a conversation between the creator and one or more chosen people, name optional. Starting a direct message with exactly the same set of people opens the existing one instead of creating a second | `src/lib/components/layout/Sidebar/ChannelModal.svelte:210-211`, `:256-260`; `backend/open_webui/routers/channels.py:320-342`; `backend/open_webui/models/channels.py:432-466` |
| Member, membership | A `channel_member` row: status `joined`, `is_active`, `last_read_at`, who invited the person and when. Group channel and direct message members are added on purpose; in a standard channel a row is created the first time the person opens it or posts in it | `backend/open_webui/models/channels.py:297-325`, `:528-564`; `backend/open_webui/routers/channels.py:824`; `backend/open_webui/models/messages.py:144` |
| Active and hidden | `is_active` false hides a channel from that person's list and blocks them in group channels and direct messages. Hiding a direct message with **×** sets it; a new message in a group channel or direct message sets every member active again | `backend/open_webui/models/channels.py:651-686`; `backend/open_webui/routers/channels.py:1165-1169` |
| Creator, manager | The person who created the channel (`channel.user_id`). The creator is the channel's manager; a `manager` membership role exists in the code but nothing assigns it (section 3.3) | `backend/open_webui/models/channels.py:510-526` |
| Message | A post in a channel: text in Markdown, optional files and model output, author, times. Stored in `message` | `backend/open_webui/models/messages.py:38-58` |
| Thread | Replies attached to one top-level message (`parent_id`). They appear only in the thread panel; the main list shows "{n} Replies - Last reply …" under the parent | `backend/open_webui/models/messages.py:281-292`; `src/lib/components/channel/Messages/Message.svelte:641-662` |
| Reply (quote reply) | A message that quotes another (`reply_to_id`); the quoted message is shown above it, and clicking it scrolls to the original. The composer shows "Replying to {NAME}" | `src/lib/components/channel/Messages/Message.svelte:316-374`; `src/lib/components/channel/MessageInput.svelte:814-835` |
| Reaction | An emoji short code added by a person to a message; one row per person per emoji. Clicking an existing reaction toggles your own | `backend/open_webui/models/messages.py:19-35`, `:448-470`; `src/lib/components/channel/Messages.svelte:195-254` |
| Pin | A flag on a message with who pinned it and when; any writer can pin or unpin any message. Pinned messages show a **Pinned** label and are listed under **Pinned Messages** | `backend/open_webui/models/messages.py:48-51`, `:415-428`; `src/lib/components/channel/Messages/Message.svelte:307-314` |
| Mention | A token the composer inserts when you pick a name from the `@` or `#` list: `<@U:{id}|{name}>` for a person, `<@M:{id}|{name}>` for a model, `<#C:{id}|{name}>` for a channel. Typing the name without picking it from the list is plain text | `src/lib/components/channel/MessageInput/MentionList.svelte:84-96`; `src/lib/components/common/RichTextInput.svelte:118-126`; `backend/open_webui/utils/channels.py:4-31` |
| Model reply | A message the server creates when a model is mentioned; stored with the model's id and name in `meta` and under the user id of the person who mentioned it | `backend/open_webui/routers/channels.py:1023-1039` |
| Model Response Mode | Where a model answers a top-level message: **Thread** (default; the answer starts a thread under the message) or **Channel** (the answer is posted in the main list). Replies inside a thread always stay in that thread | `backend/open_webui/routers/channels.py:1015-1021`; `backend/open_webui/config.py:2030` |
| Incoming webhook | A named sender, with an optional picture, that an outside system uses to post into one channel through a secret URL. Its messages show the webhook's current name; after the webhook is deleted they show `Deleted Webhook` | `backend/open_webui/models/channels.py:186-200`; `backend/open_webui/models/messages.py:199-213` |
| Unread count | The number of top-level messages from other people (and webhooks and model replies posted under other people) newer than your `last_read_at` in that channel. Thread replies and your own messages are not counted | `backend/open_webui/models/messages.py:430-446`; `backend/open_webui/routers/channels.py:183-189` |
| Typing indicator | "{names} is typing..." under the message box, sent while someone types and cleared after 5 seconds | `src/lib/components/channel/MessageInput.svelte:754-768`; `src/lib/components/channel/Channel.svelte:198-224` |
| Channel room | The live-update group `channel:{id}` that each signed-in browser joins for every channel in its list; new messages, edits, reactions and typing are sent to it | `backend/open_webui/socket/main.py:479-484`, `:555-581` |
| Channel chat id | `channel:{id}`: the conversation id a model reply runs under, so tools, filters and the live updates know the reply belongs to a channel | `backend/open_webui/routers/channels.py:1111-1119`; `backend/open_webui/socket/main.py:1134-1137` |
| Channel automation | An automation whose target is a channel, so its result is posted there (see `automations-calendar-and-timers.md`) | `backend/open_webui/routers/automations.py:114-135`; `backend/open_webui/utils/automations.py:260-283` |

Mentioning a person does not notify them in any special way: the server reads only model mentions
from a message (`backend/open_webui/routers/channels.py:979-996`); people are notified of channel
messages in general (section 9). When a viewer cannot see the model or channel a mention points
to, it is shown as `@Unknown` or `#Unknown`
(`src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte:56-79`).
Clicking a model mention opens a new chat with that model; clicking a channel mention opens the
channel (`:90-108`).

## 5. Workflows (Step by Step)

Tier 1 does not change settings, permissions, membership or content. The steps below describe what
users and admins do, so support can follow along and tell them where to look.

### 5.1 Switch Channels On for the Site (Admin)

1. Open **Admin Settings › General** (`/admin/settings/general`) and find **Channels** in the
   **Features** section, described as "Allow users to use channels for shared conversations."
   (`src/lib/components/admin/Settings/General.svelte:274`, `:342-348`;
   `src/lib/i18n/locales/en-US/translation.json:2375-2376`).
2. Turn the switch on. **Model Response Mode** appears under it with **Thread** and **Channel**
   (`src/lib/components/admin/Settings/General.svelte:349-363`).
3. Save. The server stores `channels.enable` and `channels.model_response_mode`; a mode other than
   `thread` or `channel` is ignored (`backend/open_webui/routers/auths.py:1269-1296`, `:1286-1287`).
4. People see the **Channels** section after their page reloads, because the sidebar reads the
   `enable_channels` value the browser fetched from `/api/config` at start-up
   (`backend/open_webui/main.py:2356`; `src/lib/components/layout/Sidebar.svelte:406-411`).
5. To restrict Channels to some people, turn **Channels** off under **Default permissions** and on
   in the chosen groups (**Admin Panel › Users › Groups**, **Features Permissions**;
   `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:994-1008`). The default is on
   (`backend/open_webui/config.py:1922`).

### 5.2 Create a Standard Channel (Admin Only)

1. In the sidebar **Channels** section press **+** (**Create Channel**). The dialog opens with
   **Channel Type** set to **Channel** for admins
   (`src/lib/components/layout/Sidebar/ChannelModal.svelte:77-84`, `:169-203`). The hint under it
   reads "Discussion channel where access is based on groups and permissions" (`:206-207`).
2. Type a **Channel Name** (placeholder `new-channel`). Spaces become hyphens and letters become
   lower case as you type; more than 128 characters is refused with
   `Channel name must be less than 128 characters` (`:41-43`, `:58-63`, `:224-232`). An empty name is
   refused with `Channel name cannot be empty.` (`src/lib/components/layout/Sidebar.svelte:848-851`).
3. In the access panel choose **Private** (only the people and groups in **Access List**) or
   **Public** (everyone can read). With **Public**, **Allow public write access** lets everyone
   post; otherwise people need a **Write** entry to post
   (`src/lib/components/workspace/common/AccessControl.svelte:517-560`, `:571-627`). With no entries
   the panel reads `No access grants. Private to you.` (`:698-700`).
4. Press **Create**. The server lower-cases the name, stores the channel and its grants, tells
   every member's browser `channel:created` (for a standard channel nobody is a member yet, so this
   reaches no one), and the creator is taken to `/channels/{id}`
   (`backend/open_webui/routers/channels.py:344-362`; `backend/open_webui/models/channels.py:343-377`;
   `src/lib/components/layout/Sidebar.svelte:855-873`).
5. Other people see a new standard channel in their list the next time their sidebar loads the
   channel list (page load, or another `channel:created` event), not at once
   (`src/routes/+layout.svelte:797-810`).

### 5.3 Create a Group Channel and Add Members

1. Press **+** in the sidebar **Channels** section and choose **Group Channel** (the first choice
   for non-admins). The hint reads "Collaboration channel where people join as members"
   (`src/lib/components/layout/Sidebar/ChannelModal.svelte:208-209`).
2. Type a name and choose **Visibility**: **Private** ("Only invited users can access", the default)
   or **Public** ("Visible to all users") (`src/lib/components/layout/Sidebar/ChannelModal.svelte:47-55`,
   `:240-251`; `src/lib/components/workspace/common/Visibility.svelte:41-50`). The choice changes only
   the icon (section 4).
3. Press **Create**. The dialog has no people picker for group channels, so the creator is the only
   member at first (`src/lib/components/layout/Sidebar/ChannelModal.svelte:256-260`;
   `backend/open_webui/models/channels.py:275-295`, `:343-377`).
4. In the channel, press the member count in the top bar, then **Add Member**. **Add Members**
   offers people and, for groups, the groups the creator belongs to (admins see every group)
   (`src/lib/components/channel/ChannelInfoModal/UserList.svelte:114-125`;
   `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:52-105`;
   `src/lib/components/workspace/common/MemberSelector.svelte:93-97`;
   `backend/open_webui/routers/groups.py:36-52`).
5. Press **Add**. The server adds each chosen person and every **current** member of each chosen
   group; people added later to that group are not added to the channel
   (`backend/open_webui/models/channels.py:275-295`, `:468-492`). Success shows
   `Members added successfully` (`src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:32-35`).
6. The new members are not told in real time: no live event is sent when members are added
   (`backend/open_webui/routers/channels.py:628-663`). The channel appears in their sidebar, and
   live updates for it start, after they reload the page (`backend/open_webui/socket/main.py:479-484`).
7. To remove someone, the creator presses the **×** beside the member (their own row is disabled).
   Success shows `Member removed successfully`; the membership row is deleted and the person's
   earlier messages stay (`src/lib/components/channel/ChannelInfoModal.svelte:44-58`;
   `src/lib/components/channel/ChannelInfoModal/UserList.svelte:258-271`;
   `backend/open_webui/models/channels.py:494-508`).

### 5.4 Start, Find, Hide and Reopen a Direct Message

1. Either press **+** and choose **Direct Message** ("Private conversation between selected users"),
   pick one or more people and press **Create**, or open a person's profile preview (click their
   picture in a channel or member list) and press **Message**
   (`src/lib/components/layout/Sidebar/ChannelModal.svelte:210-211`, `:256-260`;
   `src/lib/components/channel/Messages/Message/UserStatus.svelte:117-137`). The name is optional.
   Creating with nobody chosen shows
   `Please select at least one user for Direct Message channel.`
   (`src/lib/components/layout/Sidebar.svelte:843-847`).
2. If a direct message with exactly the same people already exists, it is reopened instead of a
   new one being made, and it is shown again in the starter's list
   (`backend/open_webui/routers/channels.py:247-261`, `:320-342`;
   `backend/open_webui/models/channels.py:432-466`).
3. Every participant's browser receives `channel:created` and reloads its channel list, so the
   conversation appears for the other people straight away
   (`backend/open_webui/routers/channels.py:345-354`; `src/routes/+layout.svelte:796-810`).
4. In the sidebar a direct message shows the other people's names (and, with one other person,
   their status message and a green dot when they are active)
   (`src/lib/components/layout/Sidebar/ChannelItem.svelte:115-191`).
5. **Hide** it with the **×** on its row. This marks only the caller's membership inactive; the
   others keep it, nothing is deleted (`src/lib/components/layout/Sidebar/ChannelItem.svelte:205-229`;
   `backend/open_webui/routers/channels.py:591-615`).
6. It comes back when anyone posts in it (every member is made active again) or when the person
   starts a direct message with the same people (`backend/open_webui/routers/channels.py:1165-1169`,
   `:260`, `:334`). While hidden, the person cannot open or post in it
   (`backend/open_webui/models/channels.py:675-686`).
7. Direct messages cannot be renamed, deleted or given new members from the screens: their row has
   only the **×** button (`src/lib/components/layout/Sidebar/ChannelItem.svelte:205-243`), and their
   member list has no add or remove buttons (`src/lib/components/channel/ChannelInfoModal.svelte:117-128`).

### 5.5 Post, Reply, Use Threads, React, Pin and Attach Files

1. **Post.** Type in the message box (placeholder `Type here...`) and press Enter (Shift+Enter for a
   new line, unless the person's settings use Ctrl+Enter to send) or the send button
   (`src/lib/components/channel/Channel.svelte:400-416`;
   `src/lib/components/channel/MessageInput.svelte:906-960`). The message appears at once, faded
   until the server confirms it (`src/lib/components/channel/Channel.svelte:228-266`;
   `src/lib/components/channel/Messages.svelte:134-135`).
2. **Suggestions.** `@` lists people (members of this channel first, then everyone else the user
   search returns) and models; `#` lists channels; `/` inserts saved prompts; `:` inserts emoji
   (`src/lib/components/channel/MessageInput.svelte:570-640`;
   `src/lib/components/channel/MessageInput/MentionList.svelte:43-78`, `:145-160`). A saved prompt
   that uses variables such as `{{USER_EMAIL}}` or `{{USER_LOCATION}}` is filled in before posting,
   so the value is shared with everyone in the channel
   (`src/lib/components/channel/MessageInput.svelte:106-222`).
3. **Reply.** Hover a message and press **Reply** (or swipe right on a touch screen). The box shows
   "Replying to {NAME}"; Escape or **×** cancels
   (`src/lib/components/channel/Messages/Message.svelte:236-247`, `:89-138`;
   `src/lib/components/channel/MessageInput.svelte:814-835`, `:963-966`).
4. **Thread.** **Reply in Thread** opens the **Thread** panel; its box reads `Reply to thread...`.
   Thread replies do not appear in the main list; the parent shows "{n} Replies - Last reply …"
   (`src/lib/components/channel/Messages/Message.svelte:264-275`, `:641-662`;
   `src/lib/components/channel/Thread.svelte:144-160`, `:245-261`).
5. **React.** **Add Reaction** opens the emoji picker; pressing an existing reaction adds or removes
   your own. Hovering a reaction lists who reacted ("{{NAMES}} reacted with {{REACTION}}")
   (`src/lib/components/channel/Messages/Message.svelte:215-234`, `:560-639`;
   `src/lib/components/channel/Messages.svelte:195-254`).
6. **Pin.** **Pin** or **Unpin** on any message; the top bar's **Pinned Messages** lists them, and
   unpinning from that list is possible there too
   (`src/lib/components/channel/Messages/Message.svelte:249-262`;
   `src/lib/components/channel/PinnedMessagesModal.svelte:105-132`;
   `backend/open_webui/routers/channels.py:1358-1424`). A person without write access in a standard
   channel can press **Pin** in the **Pinned Messages** list, but the server refuses it
   (`src/lib/components/channel/PinnedMessagesModal.svelte:106-131`;
   `backend/open_webui/routers/channels.py:1375-1378`).
7. **Files and images.** Use **More** › **Upload Files** or **Capture** (screen capture), drag and
   drop, or paste (`src/lib/components/channel/MessageInput/InputMenu.svelte:42-69`;
   `src/lib/components/channel/MessageInput.svelte:513-540`, `:967-981`). Each file is uploaded with
   the channel's id and recorded against the channel, then against the message when it is posted
   (`src/lib/components/channel/MessageInput.svelte:440-506`;
   `backend/open_webui/routers/files.py:430-433`;
   `backend/open_webui/routers/channels.py:1229-1236`). The site's maximum file size applies
   (`src/lib/components/channel/MessageInput.svelte:364-378`). Images may be resized before upload
   when the person's image compression setting for channels is on or the site sets a size limit
   (`:380-430`). Images and videos are shown inline; other files as file cards
   (`src/lib/components/channel/Messages/Message.svelte:459-487`).
8. **Who can open the files.** Anyone who can read a channel can open a file attached in it
   (`backend/open_webui/utils/access_control/files.py:66-69`;
   `backend/open_webui/models/channels.py:715-776`); see `files-uploads-and-storage.md`.

### 5.6 Mention a Model and How Its Reply Is Produced

1. Type `@` and pick a model from the **Models** part of the list. Only models in the person's own
   model list are offered, and their own direct-connection models are left out
   (`src/lib/components/channel/MessageInput/MentionList.svelte:153-158`, `:193-203`). Picking it
   inserts a mention token; typing the model's name by hand does not (section 4).
2. Post the message. The server saves it, sends it to the channel's room, and starts a background
   task that first produces any model replies and then sends notifications
   (`backend/open_webui/routers/channels.py:1228-1252`).
3. The task decides which models answer: every model mentioned in the message, plus the model that
   wrote the message being replied to (a **Reply** to a model's message brings that model back
   without a new mention) (`backend/open_webui/routers/channels.py:979-999`).
4. It looks each model up in **the poster's** filtered model list; a model the poster cannot use is
   skipped without any message (`backend/open_webui/routers/channels.py:977`, `:1001-1005`).
5. Where the reply goes: inside a thread it stays in that thread; for a top-level message it starts
   a thread under the message when **Model Response Mode** is **Thread** (the default) and goes into
   the main list when it is **Channel** (`backend/open_webui/routers/channels.py:1015-1021`).
6. An empty reply message is created at once, labelled with the model's name and picture and shown
   as a loading placeholder; it is stored under the poster's account
   (`backend/open_webui/routers/channels.py:1023-1039`;
   `src/lib/components/channel/Messages/Message.svelte:383-394`, `:427-428`, `:543-544`).
7. What the model is given (`backend/open_webui/routers/channels.py:1041-1100`):
   - a system message: `You are {name}, participating in a threaded conversation. Be concise and conversational.`
     followed, when there is history, by the thread's messages as "{display name}: {text}" lines and
     `Continue the conversation naturally as {name}, addressing the most recent message while being aware of the full context.`
   - the history is the thread only: its 50 most recent replies, plus the thread's first message
     when there are fewer than 50 replies; the rest of the channel's main list is **not** included
     (`backend/open_webui/models/messages.py:319-345`);
   - the new message as "{poster name}: {text}";
   - images attached anywhere in that thread (read with the poster's file access), and other files
     in the thread, which go through the normal file retrieval (`files`).
   Everyone's display names and words in the thread therefore go to the model's provider.
8. The model's own defaults are applied: its default tools, filters and terminal, and its default
   web search or image generation features when the model has that capability and the admin has
   the feature on. Code interpreter is never used here
   (`backend/open_webui/utils/automations.py:166-199`; `backend/open_webui/routers/channels.py:1103-1123`).
9. The request runs through the normal chat completion pipeline as the poster, with the channel
   chat id `channel:{id}` (`backend/open_webui/routers/channels.py:1105-1129`). Tools run with **Full
   access** (`backend/open_webui/main.py:1255-1263`).
10. As the answer streams, the reply message is updated about six times a second, then marked done;
    files the model produces are attached to the reply; tool and reasoning steps are shown as
    structured output (`backend/open_webui/socket/main.py:1019-1131`;
    `src/lib/components/channel/Messages/Message.svelte:536-542`). The fork's **Hide Processing
    Details** setting decides whether processing steps count as structured output in channels too
    (section 12).
11. If the pipeline reports an error, the reply's text becomes `Error: {error_content}` (default
    `An error occurred`) (`backend/open_webui/socket/main.py:1126-1129`). If the pipeline cannot
    start at all, the error is only written to the server log and the reply can stay an empty
    placeholder (`backend/open_webui/routers/channels.py:1131-1132`).

### 5.7 Edit and Delete a Message

1. **Edit**: hover your message, press **Edit**, change the text, then **Save** (or Ctrl/Cmd+Enter);
   **Cancel** or Escape leaves it unchanged (`src/lib/components/channel/Messages/Message.svelte:277-290`,
   `:489-533`). The text is replaced, attachments and details are merged, and everyone viewing sees
   the change live (`backend/open_webui/models/messages.py:396-413`;
   `backend/open_webui/routers/channels.py:1530-1547`). Edited messages (other than model replies)
   show `(edited)` (`src/lib/components/channel/Messages/Message.svelte:553-556`). Editing does not
   ask a mentioned model to answer again: only posting does (`backend/open_webui/routers/channels.py:1494-1560`).
2. **Delete**: press **Delete**; the confirmation is titled **Delete Message** and asks
   `Are you sure you want to delete this message?` (`src/lib/components/channel/Messages/Message.svelte:158-165`,
   `:292-301`). The message disappears from the screen straight away, before the server answers
   (`src/lib/components/channel/Messages.svelte:141-150`).
3. What deletion removes: the message row and its reactions, permanently; there is no undo or
   recycle bin (`backend/open_webui/models/messages.py:588-596`). It does **not** remove the thread
   replies under it, which stay in the database but can no longer be opened from the screens
   (the main list shows only top-level messages and a thread needs its first message)
   (`backend/open_webui/models/messages.py:281-292`, `:328-332`; a cleanup function exists but
   nothing calls it, `:582-586`). Files attached to the message stay in file storage.
4. Who may edit or delete: the author or an admin (section 3.2); in group channels and direct
   messages the admin must also be a member.

### 5.8 Rename, Change or Delete a Channel

1. The creator or an admin presses the gear on the channel's sidebar row to open **Edit Channel**
   (`src/lib/components/layout/Sidebar/ChannelItem.svelte:230-243`). Name, visibility (group) or
   access (standard) can be changed; **Update** saves and shows `Channel updated successfully`
   (`src/lib/components/layout/Sidebar/ChannelItem.svelte:55-78`).
2. Saving also clears the channel's description and other details that the dialog does not show,
   because the server writes every field it receives (`backend/open_webui/models/channels.py:830-851`;
   the dialog sends only name, visibility, access and members,
   `src/lib/components/layout/Sidebar/ChannelItem.svelte:61-68`). No screen shows a description in
   this version.
3. Other members are not told live about the change; they see it when their channel list next
   loads (`backend/open_webui/routers/channels.py:709-746`).
4. **Delete** asks `Are you sure you want to delete this channel?`; on success it shows
   `Channel deleted successfully` and, if you were in that channel, takes you to the home page
   (`src/lib/components/layout/Sidebar/ChannelModal.svelte:107-130`, `:317-324`).
5. What deletion removes: the `channel` row and its access grants, permanently
   (`backend/open_webui/models/channels.py:912-917`). No code removes the channel's messages,
   reactions, memberships or webhooks; messages, reactions and memberships remain in the database,
   unreachable from the screens. The links between the channel and its files, and (in the table the
   migration creates) the channel's webhooks, are declared to be removed with the channel; PostgreSQL
   enforces this, SQLite only with foreign-key enforcement on, which this code does not switch on
   (`backend/open_webui/models/channels.py:157-169`;
   `backend/open_webui/migrations/versions/90ef40d4714e_update_channel_and_channel_members_table.py:53-69`;
   `backend/open_webui/internal/db.py:335-391`).
   The `archived_at` and `deleted_at` columns exist and the lists skip rows that have them, but
   nothing in this version sets them (`backend/open_webui/models/channels.py:61-65`, `:402-403`).
6. Others still in the channel are not told; their next action in it fails and the page sends them
   home (`backend/open_webui/routers/channels.py:754-788`; `src/lib/components/channel/Channel.svelte:124-140`).
   The channel's webhooks stop working (section 5.9).

### 5.9 Incoming Webhooks

1. The creator or an admin opens **Edit Channel**, then **Webhooks** › **Manage**
   (`src/lib/components/layout/Sidebar/ChannelModal.svelte:262-276`). The **Webhooks** window shows a
   count and the list, or `No webhooks yet` (`src/lib/components/channel/WebhooksModal.svelte:99-162`).
2. **New Webhook** creates one straight away, named `New Webhook`
   (`src/lib/components/channel/WebhooksModal.svelte:44-58`, `:109-117`). Each row shows the
   picture, name and "Created on {date}" (`src/lib/components/channel/WebhookItem.svelte:92-123`).
3. Press a row to expand it: change the picture (click it; GIF and WebP files are kept as they are,
   other images are reduced to 100 by 100 pixels), change **Name** (placeholder `Webhook Name`),
   **Copy URL**, or **Delete** (`src/lib/components/channel/WebhookItem.svelte:38-71`, `:126-174`).
   **Save** stores name and picture changes and shows `Saved`
   (`src/lib/components/channel/WebhooksModal.svelte:60-73`).
4. **Copy URL** copies the webhook's posting address to the clipboard and shows `Copied`; the address
   is not displayed (`src/lib/components/channel/WebhookItem.svelte:73-78`). The address contains a
   secret, and **whoever holds it can post into the channel without signing in**
   (`backend/open_webui/routers/channels.py:2005-2023`). Treat it like a password: never paste it
   into a ticket, chat or document. Its location in the database is the `channel_webhook` table
   (section 6); its value is not reproduced anywhere in this knowledgebase.
5. The outside system sends message text (text only: the incoming form has a single content field,
   so no files) to that address (`backend/open_webui/routers/channels.py:2001-2002`). The message
   appears live under the webhook's name and picture, with no profile preview, and the webhook's
   "last used" time is updated (`backend/open_webui/routers/channels.py:2025-2075`;
   `src/lib/components/channel/Messages/Message.svelte:395-399`).
6. Webhook messages do not make models answer and do not trigger the per-person notification
   targets (no model or notification step runs on this path; compare
   `backend/open_webui/routers/channels.py:2005-2084` with `:1243-1252`). Browsers in the channel's
   room still show the usual pop-up for them (section 9).
7. A webhook's address cannot be changed: renaming or a new picture keeps the same address
   (`backend/open_webui/models/channels.py:975-990`). Deleting the webhook is the only way to stop
   an address working; its earlier messages then show the sender `Deleted Webhook`
   (`backend/open_webui/models/messages.py:207-213`). A suspected leak of a webhook address is a
   security matter: refer it to U of T Information Security (security.utoronto.ca).
8. A picture given as a web address is fetched for viewers only when
   `ENABLE_PROFILE_IMAGE_URL_FORWARDING` is on (code default on); otherwise the default logo shows
   (`backend/open_webui/env.py:970`; `backend/open_webui/routers/channels.py:1846-1874`).

### 5.10 Unread Counts and Read Tracking

1. Opening a channel, leaving it, and typing in it send a "read up to now" signal over the live
   connection, which updates `last_read_at` on the person's membership; the sidebar count is set to
   zero at once (`src/lib/components/channel/Channel.svelte:64-84`, `:107-114`, `:268-281`,
   `:304-307`; `backend/open_webui/socket/main.py:555-581`).
2. The server only accepts that signal from a browser connection that is in the channel's room
   (`backend/open_webui/socket/main.py:557-559`). A connection joins rooms when it signs in, so for a
   channel the person was added to after their page loaded, reading is not recorded until they
   reload (`backend/open_webui/socket/main.py:479-484`).
3. The count shown on page load comes from the server: top-level messages from others since
   `last_read_at` (`backend/open_webui/routers/channels.py:180-191`;
   `backend/open_webui/models/messages.py:431-446`). A standard channel the person has never opened
   has no membership row and shows no count (`backend/open_webui/routers/channels.py:186-191`).
4. While the page is open, every new-message event from someone else in a channel the person is not
   viewing adds one to the count, thread replies included, so the number can drop after a reload
   (`src/routes/+layout.svelte:827-847`).

### 5.11 Channel Automations

An automation can post its result into a channel. The automations router accepts a channel target
only when Channels are on and the owner can use that channel, and the run posts with the same
thread or channel placement as a model reply (`backend/open_webui/routers/automations.py:114-135`;
`backend/open_webui/utils/automations.py:260-283`). The `create_automation` tool sets the current
channel as the target when it is used from a channel reply (`backend/open_webui/tools/builtin.py:3788-3792`).
Details are in `automations-calendar-and-timers.md`.

## 6. Data Model

All six tables live in the relational database (SQLite by default, or PostgreSQL; which one
production uses is **TO BE CONFIRMED**, ground truth). Times are integers: nanoseconds since
1970 for channels, members, messages, reactions and webhooks, but **seconds** for `channel_file`
(`backend/open_webui/models/channels.py:354-355`, `:863-864`). The tables hold personal and
possibly health information; only approved staff may query them, read-only and in aggregate
(no message text in tickets).

### 6.1 `channel`

| Column | Meaning | Notes | Source |
|---|---|---|---|
| `id` | Channel id (UUID) | Appears in `/channels/{id}` | `backend/open_webui/models/channels.py:43` |
| `user_id` | Creator | The creator is the manager (section 3.3) | `:44` |
| `type` | Empty or null (standard), `group`, `dm` | | `:45` |
| `name` | Name, lower-cased on create; empty for most direct messages | Not lower-cased again on rename by the server; the dialog lower-cases as you type | `:47`, `:351`, `:839`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:41-43` |
| `description` | Free text | No screen sets or shows it; cleared when the channel is saved from the dialog | `backend/open_webui/models/channels.py:48`, `:840` |
| `is_private` | Group channel visibility | Display only | `:50-51` |
| `data`, `meta` | Spare JSON fields | Cleared on save from the dialog | `:53-54`, `:843-844` |
| `created_at`, `updated_at` | Created and last-saved times | | `:56-58` |
| `updated_by`, `archived_at`, `archived_by`, `deleted_at`, `deleted_by` | Reserved | Nothing sets them in this version; lists skip rows with `archived_at` or `deleted_at` | `:59-65`, `:402-403` |

Access for standard channels is not in this table: it is in `access_grant` rows with
`resource_type` `channel` (read or write, for `user:*`, a person or a group), written on create and
save and removed on delete (`backend/open_webui/models/channels.py:259-273`, `:376`, `:846-847`,
`:912-917`; `users-groups-roles-and-permissions.md`).

### 6.2 `channel_member`

| Column | Meaning | Notes | Source |
|---|---|---|---|
| `id`, `channel_id`, `user_id` | Membership | One row per person per channel | `backend/open_webui/models/channels.py:97-102` |
| `role` | Membership role | Only `manager` is ever checked, and nothing sets it | `:104`, `:510-526` |
| `status` | `joined` on creation | A `left` value exists only in the unused leave function | `:105`, `:316`, `:578` |
| `is_active` | Shown in the person's list, allowed to use a group channel or direct message | Set false by hiding a direct message; set true by new messages and by reopening | `:107`, `:651-673` |
| `is_channel_muted`, `is_channel_pinned` | Reserved | Always false; no screen or endpoint changes them in this version | `:109-110`, `:607-629` |
| `data`, `meta` | Spare JSON fields | | `:112-113` |
| `invited_at`, `invited_by` | When and by whom the person was added | Empty for standard-channel rows created on first visit | `:115-116`, `:320-321`, `:544-558` |
| `joined_at`, `left_at` | Join time; leave time (unused) | | `:118-119` |
| `last_read_at` | Read position for unread counts | Updated by the read signal (section 5.10) | `:121`, `:631-649` |
| `created_at`, `updated_at` | Row times | | `:123-124` |

### 6.3 `message`

| Column | Meaning | Notes | Source |
|---|---|---|---|
| `id` | Message id | Used in `?thread={id}` | `backend/open_webui/models/messages.py:40` |
| `user_id` | Author | For a model reply, the person who mentioned the model; for a webhook post, the webhook's creator | `:42`; `backend/open_webui/routers/channels.py:1023-1039`, `:2029-2034` |
| `channel_id` | Channel | Not a database-enforced link | `backend/open_webui/models/messages.py:43` |
| `reply_to_id` | The quoted message (**Reply**) | | `:45` |
| `parent_id` | The thread's first message, for thread replies | Null for top-level messages | `:46` |
| `is_pinned`, `pinned_at`, `pinned_by` | Pin state | `pinned_by` is the person who pinned it | `:49-51`, `:415-428` |
| `content` | The text, in Markdown with mention tokens | | `:53` |
| `data` | JSON: `files` (attachments) and, for model replies, `output` (structured output) | The message list sends only "has data" and the browser fetches the detail separately | `:54`; `backend/open_webui/routers/channels.py:791-800`; `src/lib/components/channel/Messages/Message.svelte:140-151` |
| `meta` | JSON: `model_id`, `model_name`, `done` for model replies; `webhook` (the webhook id) for webhook posts | | `:55`; `backend/open_webui/routers/channels.py:1031-1034`, `:2030`; `backend/open_webui/socket/main.py:1045-1052` |
| `created_at`, `updated_at` | Posted and last-changed times | A difference marks the message `(edited)` on screen | `backend/open_webui/models/messages.py:57-58` |

### 6.4 `message_reaction`

| Column | Meaning | Source |
|---|---|---|
| `id`, `message_id`, `user_id` | One reaction by one person on one message | `backend/open_webui/models/messages.py:19-24` |
| `name` | Emoji short code; the same person cannot add the same emoji twice | `:24`, `:453-457` |
| `created_at` | Time added | `:25` |

### 6.5 `channel_file`

| Column | Meaning | Source |
|---|---|---|
| `id`, `user_id` | Link id and the uploader | `backend/open_webui/models/channels.py:160-161` |
| `channel_id`, `message_id`, `file_id` | The channel, the message (set once posted), the file in the `file` table; one row per channel and file | `:163-165`, `:170`, `:879-899` |
| `created_at`, `updated_at` | Times, in seconds | `:167-168` |

This link is what lets channel readers open the file (section 5.5). The file itself is described in
`files-uploads-and-storage.md`.

### 6.6 `channel_webhook`

| Column | Meaning | Source |
|---|---|---|
| `id`, `channel_id`, `user_id` | Webhook id, its channel and its creator | `backend/open_webui/models/channels.py:189-191` |
| `name`, `profile_image_url` | Display name and picture (a web address or an embedded image) | `:193-194`, `:247-256` |
| `token` | The secret part of the posting address. **Never read, copy or reproduce it**; it is not needed for support | `:196` |
| `last_used_at` | Time of the last post through the webhook | `:197`, `:992-1000` |
| `created_at`, `updated_at` | Times | `:199-200` |

### 6.7 Migrations

| Revision file | What it did for this area | Source |
|---|---|---|
| `57c599a3cb57_add_channel_table.py` | Created `channel` and `message` | `backend/open_webui/migrations/versions/57c599a3cb57_add_channel_table.py:23-48` |
| `3781e22d8b01_update_message_table.py` | Added channel `type` and message `parent_id`; created `message_reaction` and `channel_member` | `backend/open_webui/migrations/versions/3781e22d8b01_update_message_table.py:26-63` |
| `6283dc0e4d8d_add_channel_file_table.py` | Created `channel_file` | `backend/open_webui/migrations/versions/6283dc0e4d8d_add_channel_file_table.py:28-41` |
| `81cc2ce44d79_update_channel_file_and_knowledge_table.py` | Added `channel_file.message_id` | `backend/open_webui/migrations/versions/81cc2ce44d79_update_channel_file_and_knowledge_table.py:30-34` |
| `90ef40d4714e_update_channel_and_channel_members_table.py` | Added `is_private`, archive and delete columns, member role and invitation columns; created `channel_webhook` | `backend/open_webui/migrations/versions/90ef40d4714e_update_channel_and_channel_members_table.py:30-69` |
| `2f1211949ecc_update_message_and_channel_member_table.py` | Added member status, flags, read position; added message pins and reply target | `backend/open_webui/migrations/versions/2f1211949ecc_update_message_and_channel_member_table.py:29-92` |
| `f1e2d3c4b5a6_add_access_grant_table.py` | Moved channel access lists into `access_grant` | `backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py:62-72`, `:215-223` |

No migration is local to the fork (ground truth).

## 7. Settings and Configuration

Code defaults below are what the repository says. Live values are data in the `config` table (or
the environment for environment-only settings) and are **TO BE CONFIRMED** for production. After
first boot the stored value wins over the environment variable (ground truth).

### 7.1 Site Settings (Admin)

| Setting (label) | Key; environment variable | Code default | Where it is changed | Effect | Source |
|---|---|---|---|---|---|
| **Channels** | `channels.enable`; `ENABLE_CHANNELS` | Off | Admin Settings › General › Features | The whole feature (section 3.1) | `backend/open_webui/config.py:2028`, `:3104`; `backend/open_webui/routers/auths.py:125`; `src/lib/components/admin/Settings/General.svelte:342-348` |
| **Model Response Mode** (**Thread**, **Channel**) | `channels.model_response_mode`; `CHANNEL_MODEL_RESPONSE_MODE` | `thread` | Same place, shown only while Channels is on | Where model answers to top-level messages go (section 5.6); also used by channel automations | `backend/open_webui/config.py:2030`, `:3105`; `backend/open_webui/routers/auths.py:126`, `:1286-1287`; `src/lib/components/admin/Settings/General.svelte:349-363`; `backend/open_webui/utils/automations.py:283` |
| **Channels** permission | `features.channels` in `user.permissions`; `USER_PERMISSIONS_FEATURES_CHANNELS` | On | Admin Panel › Users › Groups › Default permissions or a group › **Features Permissions** | Who may use channels (section 3.1) | `backend/open_webui/config.py:1922`, `:2006`; `src/lib/components/admin/Users/Groups/Permissions.svelte:994-1008` |
| (no label) | `sharing.public_channels` | Not defined | No screen | Removes public grants from channels saved by non-admins (section 3.1) | `backend/open_webui/routers/channels.py:312-318`, `:726-732` |
| Access-list permissions | `access_grants.allow_users`, `access_grants.allow_groups` | See `users-groups-roles-and-permissions.md` | Group permissions | Whether a non-admin may name people or groups in an access list | `backend/open_webui/utils/access_control/__init__.py:276-299` |
| **User Webhooks** | `ui.enable_user_webhooks`; `ENABLE_USER_WEBHOOKS` | Off | Admin Settings › General | Needed for channel-message notification targets (section 9.3) | `backend/open_webui/config.py:2100`; `src/lib/components/admin/Settings/General.svelte:379-385`; `backend/open_webui/routers/auths.py:131`; `backend/open_webui/routers/channels.py:943`, `:951`; `backend/open_webui/utils/notifications.py:394` |
| Site address | `webui.url`; `WEBUI_URL` | Empty | Admin Settings › General | Start of the channel link put into notification-target messages, `{webui_url}/channels/{id}` | `backend/open_webui/config.py:1661`, `:3082`; `src/lib/components/admin/Settings/General.svelte:413`; `backend/open_webui/routers/channels.py:942`, `:949` |
| Upload limits and image size | `rag.file.max_size`, `file.image_compression_width`, `file.image_compression_height` | See `files-uploads-and-storage.md` | Admin Settings › Documents | Largest file the channel box accepts; site-wide image resizing for channel uploads | `backend/open_webui/main.py:2413-2420`; `src/lib/components/channel/MessageInput.svelte:364-378`, `:383-406` |
| Webhook picture by web address | `ENABLE_PROFILE_IMAGE_URL_FORWARDING` (environment only) | On | Environment | Whether a webhook picture given as a web address is shown | `backend/open_webui/env.py:970`; `backend/open_webui/routers/channels.py:1846-1856` |
| Embedded picture size limit | `PROFILE_IMAGE_MAX_DATA_URI_SIZE` (environment only) | No limit | Environment | Largest embedded webhook picture accepted | `backend/open_webui/env.py:982-983`; `backend/open_webui/utils/validate.py:86-91` |

Settings that look relevant but are not used here:

- `ENABLE_ADMIN_CHAT_ACCESS` and `ENABLE_ADMIN_EXPORT` are imported by the channels router but not
  used in it, so they do not change what admins can see in channels
  (`backend/open_webui/routers/channels.py:8`; a search of the file finds no other use).
- Model access settings (`BYPASS_MODEL_ACCESS_CONTROL` and model sharing) apply through the
  poster's model list (section 3.5; `workspace-models-and-model-access.md`).
- Live updates need the websocket settings described in `websockets-realtime-and-redis.md`.

### 7.2 Personal Settings That Change Channels

| Setting (label) | Where | Code default | Effect in channels | Source |
|---|---|---|---|---|
| **Browser Notifications** | Settings › Notifications | Off | Browser notification for channel messages (section 9.2); turning it on asks the browser for permission | `src/lib/components/chat/Settings/Notifications.svelte:60-78`, `:198-210`; `src/routes/+layout.svelte:866-878` |
| **Compress Images in Channels** ("Apply image compression to channel uploads too.") | Settings › Interface, under **Image Compression** | On, but only when **Image Compression** is on | Resizes images before they are uploaded to a channel | `src/lib/components/common/InterfaceSettings.svelte:1935`, `:1970-1990`; `src/lib/i18n/locales/en-US/translation.json:2894-2895`, `:2933`; `src/lib/components/channel/MessageInput.svelte:383-406` |
| **Hide Processing Details** (fork) | Settings › Interface | See section 12 | Also hides processing steps in model replies shown in channels | `src/lib/components/channel/Messages/Message.svelte:153-155`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| Rich text input, formatting toolbar, Ctrl+Enter to send, large text as file, chat direction | Settings › Interface | See `chat-composer-and-message-display.md` | The channel box uses the same settings as the chat box | `src/lib/components/channel/MessageInput.svelte:904-923` |

## 8. Cron Jobs and Background Processes

There is no crontab and no scheduled job for channels (ground truth). Channel work happens when
someone acts, partly after the server has already answered:

| What | When it runs | Where it runs | What a failure looks like | Source |
|---|---|---|---|---|
| Save and broadcast a message | During the post request | The worker that handled the request | The poster sees an error pop-up (section 10) | `backend/open_webui/routers/channels.py:1137-1213`, `:1216-1270` |
| Model replies, then notification targets | A background task started after the post is answered | The same worker, with its own short database sessions | No pop-up for the poster; errors go only to the server log; the reply may stay empty | `backend/open_webui/routers/channels.py:1240-1252`, `:1131-1132` |
| The model's answer | The chat completion pipeline, streamed | Same worker | `Error: {error_content}` in the reply | `backend/open_webui/routers/channels.py:1125-1129`; `backend/open_webui/socket/main.py:1126-1129` |
| Reply updates while streaming | At most about every 0.15 seconds, plus at tool boundaries and at the end | Same worker | Updates arrive in steps rather than word by word | `backend/open_webui/socket/main.py:1028-1029`, `:1085-1089` |
| Event publishing (`channel.created`, `message.created`, `channel.webhook.created` and the rest) | Right after each action; delivery is started as separate tasks | Same worker | Logged only (log line "Event sink failed for {event}") | `backend/open_webui/events.py:1060-1086`, `:1166-1202` |
| Joining channel rooms | When a browser connects (`user-join`) and after creating a channel (`join-channels`) | The worker holding that connection | The person gets no live updates for a channel until they reload | `backend/open_webui/socket/main.py:448-494`, `:497-516`; `src/lib/components/layout/Sidebar.svelte:868` |
| Presence (green dot, **Active** or **Away**) | The browser's heartbeat updates `last_active_at`; a person counts as active for three minutes after it | Every worker | Dots can lag by up to three minutes | `backend/open_webui/socket/main.py:489-494`; `backend/open_webui/models/users.py:911-916` |
| Channel automations | The automations scheduler loop, every `SCHEDULER_POLL_INTERVAL` seconds | Every worker (see `automations-calendar-and-timers.md`) | See that document | `backend/open_webui/utils/automations.py:260-283` |

Multi-worker points (more than one server process; see `websockets-realtime-and-redis.md`):

- With `WEBSOCKET_MANAGER=redis`, live channel events reach every worker
  (`backend/open_webui/socket/main.py:89-110`).
- Two helpers look only at connections held by the worker running the code: the list of people
  "in the room" used to skip notification targets for people who are online, and the step that adds
  participants' connections to a new direct message's room (`backend/open_webui/socket/main.py:73-75`,
  `:338-353`, `:372-385`). With several workers, people connected to another worker may therefore
  be treated as offline for notification targets, and may need to reload before a new direct
  message updates live. **TO BE CONFIRMED** by testing on the production layout.

## 9. Notifications and Emails

The application sends **no email** (ground truth). Channel activity reaches people in four ways.

### 9.1 Live Updates in the Open Page

Every browser connection that is in a channel's room receives that channel's events and updates the
open page without a reload (`backend/open_webui/socket/main.py:479-484`;
`src/lib/components/channel/Channel.svelte:143-226`; `src/lib/components/channel/Thread.svelte:65-142`):

| Event type | Sent when | Source |
|---|---|---|
| `message` | A message, thread reply, model reply placeholder or webhook post is created | `backend/open_webui/routers/channels.py:1171-1187`, `:2048-2075` |
| `message:reply` | A thread gains or loses a reply (updates the parent's reply count) | `:1189-1207`, `:1779-1797` |
| `message:update` | A message is edited, pinned or unpinned, or a model reply streams | `:1398-1411`, `:1532-1547`; `backend/open_webui/socket/main.py:1056-1067` |
| `message:reaction:add`, `message:reaction:remove` | A reaction changes | `backend/open_webui/routers/channels.py:1608-1625`, `:1683-1700` |
| `message:delete` | A message is deleted | `:1762-1777` |
| `typing` | Someone types (sent by browsers, relayed by the server to the room) | `backend/open_webui/socket/main.py:569-579` |
| `channel:created` | A channel or direct message is created, or a direct message is reopened; sent to each member personally | `backend/open_webui/routers/channels.py:253-258`, `:325-332`, `:348-354` |

No live event is sent when a channel is renamed or deleted, or when members are added or removed
(`backend/open_webui/routers/channels.py:628-788`).

### 9.2 Pop-ups and Browser Notifications

For each `message` event, the root layout decides what to show
(`src/routes/+layout.svelte:789-890`):

1. Nothing, if the message came from the person themselves (by sender id), or if they are looking
   at that channel in a visible tab. *(Corrected 2026-10-10: the first version said "a visible,
   focused tab"; in a browser only visibility is checked, and window focus is checked only in the
   desktop app, `src/routes/+layout.svelte:817-827`.)*
2. Otherwise the sidebar count goes up by one (section 5.10).
3. A **browser notification** appears only when this tab is the person's last active tab and
   **Browser Notifications** is on. Its title is "{sender name} (#{channel name}) / {app name}"
   ("{sender name} / {app name}" for a direct message); the body is the message text; the icon is
   the sender's picture (`src/routes/+layout.svelte:865-878`). With the fork's default name the app
   name is MedIT GPT (ground truth).
4. An **in-app pop-up** appears for 15 seconds with the same title (without the app name) and the
   text; clicking it opens the channel, or the thread for a thread reply
   (`src/routes/+layout.svelte:880-893`). It plays the notification sound when **Notification
   Sound** is on (code default on) and this is the last active tab
   (`src/lib/components/NotificationToast.svelte:68-84`).

Details that explain odd pop-ups:

- A model's reply is created empty under the name of the person who mentioned the model, so others
  get a pop-up with that person's name and no text when the model starts answering; the answer
  itself arrives as updates, which raise no pop-up (`backend/open_webui/routers/channels.py:1023-1039`,
  `:1171-1187`).
- Webhook posts raise pop-ups titled with the webhook's name
  (`backend/open_webui/routers/channels.py:2048-2075`).
- Mentioning a person does not raise anything extra for them (section 4).
- The person must have the channel in their room: someone added to a group channel after their page
  loaded gets no pop-ups for it until they reload (section 5.3).
- Browser notifications also need the browser's own permission; turning the setting on without it
  shows `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.`
  (`src/lib/components/chat/Settings/Notifications.svelte:60-78`).

### 9.3 Notification Targets (User Webhooks)

A person can have channel messages sent to their own notification targets (for example a chat
webhook of their choice) under **Settings › Notifications › Notification Targets**, which appears
only when the site's **User Webhooks** switch is on and the person is an admin or has the
`features.webhooks` permission (`src/lib/components/chat/Settings/Notifications.svelte:35`,
`:225-229`; `src/lib/utils/settings-access.ts:16-18`). The event is listed as **Channel message**
(`backend/open_webui/events.py:267-271`; `backend/open_webui/utils/notifications.py:223-231`).
*(Corrected 2026-10-10: the first version cited `routers/notifications.py` line 227, which is past
the end of that 103-line file; the event list for notification targets is built in
`backend/open_webui/utils/notifications.py`.)*

The server sends a `channel.message` event for a new message to each person who
(`backend/open_webui/routers/channels.py:941-973`):

1. is returned by the channel's **access grants** for read, and
2. has a membership row in the channel, and
3. had no connection in the channel's room when the message was posted (counted on the worker that
   handled the post; section 8), and
4. has saved personal settings, while the site's **User Webhooks** switch is on.

Because group channels and direct messages have no access grants (they use membership), **no
notification-target messages are sent for group channels or direct messages** in this version;
only standard channels qualify, and only for people who have opened the channel at least once
(membership). Webhook posts and model replies never send them (section 5.9, section 5.6). Delivery
then follows the person's target settings; for channel messages the "only when away" choice does
not hold anything back, because the online check was already made
(`backend/open_webui/utils/notifications.py:393-419`). The message sent is titled
"**#{channel name}**" with the text and the channel link (`backend/open_webui/utils/notifications.py:307-322`).
See `notifications-webhooks-events-and-banners.md` for targets in general.

### 9.4 Site Event Webhooks and Event Functions

Every channel action is also published as a site event (`channel.created`, `channel.updated`,
`channel.deleted`, `channel.member_added`, `channel.member_removed`,
`channel.member_active_updated`, `channel.webhook.created`, `channel.webhook.updated`,
`channel.webhook.deleted`, `message.created`, `message.updated`, `message.deleted`,
`message.reaction_added`, `message.reaction_removed`, `message.pinned`, `message.unpinned`)
(`backend/open_webui/events.py:215-285`). These go to the admin's event webhooks and to Event
functions (`backend/open_webui/events.py:1067-1171`). `message.created` and `message.updated` carry
the first 300 characters of the message (`backend/open_webui/routers/channels.py:1254-1263`,
`:1549-1555`, `:2077-2083`), so channel text can leave MedIT GPT through a configured event webhook.
Which event webhooks production has, and whether they may receive channel content, is
**TO BE CONFIRMED** (see `notifications-webhooks-events-and-banners.md`).

## 10. Error, Warning and Notice Messages (Verbatim)

How messages reach the screen in this area:

- Every channel request in the browser goes through `src/lib/apis/channels/index.ts`. When the
  server refuses, the client throws the server's `detail` text itself
  (`src/lib/apis/channels/index.ts:26-41`, the same pattern in every function). Most screens print
  that text as a red pop-up (``toast.error(`${error}`)``), so the backend messages below are what
  people see.
- When a request fails without a server reply (network down, a proxy error page that is not
  JSON), the client throws nothing and returns no result, so **no pop-up appears**
  (`src/lib/apis/channels/index.ts:33-41`).
- The server uses the same few texts for many different refusals. `Something went wrong :/`
  covers both "you are not allowed" and "the server failed"; the trigger column says how to tell
  them apart.

### 10.1 Messages From the Server

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Channels is disabled` | Error (HTTP 403) | `backend/open_webui/routers/channels.py:143-147`, also on the webhook address `:2014`; text `backend/open_webui/constants.py:125` | The site switch `channels.enable` is off; every channel request is refused, admins included | None: the feature is off for the whole site | Ask the person when it last worked; whether Channels should be on is an admin decision (section 7.1). Seen in pop-ups such as sending (`src/lib/components/channel/Channel.svelte:257`) and creating (`src/lib/components/layout/Sidebar.svelte:863`); an outside system posting to a webhook receives it as the reply |
| `401 Unauthorized` | Error (HTTP 401; HTTP 403 for webhooks) | `backend/open_webui/routers/channels.py:149-156`, `:305-310`, `:1890-1891`, `:1910-1911`, `:1942-1943`, `:1977-1978`; text `backend/open_webui/constants.py:69` | (a) A non-admin without the `features.channels` permission makes any channel request; (b) a non-admin asks to create a standard channel (the screens do not offer it); (c) someone who is neither the channel's creator nor an admin lists, creates, changes or deletes the channel's webhooks | (a) Ask an admin for Channels access; (c) ask the channel's creator | Check the person's role and group permissions (`users-groups-roles-and-permissions.md`); for (c) the creator is the only manager (section 3.3) |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/channels.py:393-394` and the same check in every channel endpoint; `:601-605`; `:1299-1300`, `:1509-1510`; `:1946-1947`, `:1981-1982`; `:2025-2026`; text `backend/open_webui/constants.py:78` | The channel was deleted; the message was deleted; a webhook does not belong to the channel; or the person's own membership is hidden or missing when the screen shows or hides the channel for them | Reload; a deleted channel or message cannot be brought back (sections 5.7 and 5.8) | Ask for the channel address (`/channels/{id}`) and when it was last seen. Opening a deleted channel shows nothing and goes to the home page instead (`src/lib/components/channel/Channel.svelte:124-140`) |
| `Something went wrong :/` | Error (HTTP 403 or 400) | 403 checks such as `backend/open_webui/routers/channels.py:400-401`, `:434-435`, `:641-642`, `:1141-1153`, `:1373-1378`, `:1515-1528`, `:1741-1758`; 400 checks such as `:1155-1160`, `:1302-1303`, `:1914-1915`, `:1950-1951`; failure branches such as `:287-288`, `:367-368`, `:1212-1213`, `:1269-1270`; text `backend/open_webui/constants.py:16-18`, `:41` | **403:** not an active member of the group channel or direct message (including a hidden direct message); no read or write grant on the standard channel; not the author of the message being edited or deleted; not the creator or an admin when changing members, settings or deleting the channel. **400:** the quoted or thread message is in another channel or no longer exists; a webhook could not be saved; or the server failed unexpectedly | Reload. For access, ask the channel's creator (group channel) or an admin (standard channel) | Ask exactly what the person did. A permission cause is usual; compare with section 3.2. Repeated 400s with no permission cause point to a server problem: escalate with the time, channel address and action |
| `[ERROR: Failed to create message]` | Error (HTTP 400) | `backend/open_webui/routers/channels.py:2036-2040`; format `backend/open_webui/constants.py:16-23` | An outside system posted through a webhook and the server could not save the message | The outside system's owner retries later | Seen only by the outside system, never in MedIT GPT; escalate with the time and channel |
| `The URL you provided is invalid. Please double-check and try again.` | Error (HTTP 401) | `backend/open_webui/routers/channels.py:2016-2022`; text `backend/open_webui/constants.py:99` | An outside system posted to a webhook address whose webhook was deleted, or whose secret part is wrong | The channel's creator makes a new webhook and passes its address to the system's owner by a secure route | Section 11.6. Never ask for, or accept, the address itself in a ticket |
| `Invalid profile image URL: data URI exceeds the {PROFILE_IMAGE_MAX_DATA_URI_SIZE}-byte limit.` | Error (HTTP 422, inside a list) | `backend/open_webui/utils/validate.py:86-91`, applied by `backend/open_webui/models/channels.py:247-256` | Saving a webhook picture (GIF and WebP pictures are kept at full size, `src/lib/components/channel/WebhookItem.svelte:46-47`) larger than the environment limit `PROFILE_IMAGE_MAX_DATA_URI_SIZE` (no limit by default, `backend/open_webui/env.py:982-983`) | Choose a smaller picture or a PNG or JPEG one, which the screen shrinks | The screen shows `[object Object]` instead of this text (section 10.2) |
| `Invalid profile image URL: must be a known internal path, an HTTP(S) URL with a host, or a data:image URI (png/jpeg/gif/webp).` | Error (HTTP 422, inside a list) | `backend/open_webui/utils/validate.py:93-96`, applied by `backend/open_webui/models/channels.py:247-256` | A webhook picture in a form the server does not accept, for example when `PROFILE_IMAGE_ALLOWED_MIME_TYPES` has been narrowed (default PNG, JPEG, GIF and WebP, `backend/open_webui/env.py:971-977`) | Choose a PNG, JPEG, GIF or WebP picture | As above |
| `Deleted Webhook` | Notice (sender name) | `backend/open_webui/models/messages.py:198-213`, `:232-247` | A message posted through a webhook that has since been deleted | None | Expected after a webhook is deleted (section 5.9) |
| `Webhook` | Notice (sender name) | `backend/open_webui/routers/channels.py:910-917`; `:2028-2030` | Every webhook post, in the **Pinned Messages** list only: a webhook post stores just the webhook's id, so that list cannot show the webhook's name | None | Expected; the main list and threads show the webhook's current name |
| `Error: {error_content}` | Error (text of the model's reply) | `backend/open_webui/socket/main.py:1126-1129` | The chat pipeline reported an error while a mentioned model was answering; `{error_content}` is the pipeline's error text | Try again later or mention another model | Note the model, channel and time; provider errors are covered in `chat-completion-pipeline-and-generation-tasks.md`; escalate |
| `Error: An error occurred` | Error (text of the model's reply) | `backend/open_webui/socket/main.py:1128-1129` | As above, when the pipeline gave no error text | As above | As above |
| `**#{channel_name}**` | Notice (sent outside MedIT GPT) | `backend/open_webui/utils/notifications.py:307-322`; built from `backend/open_webui/routers/channels.py:941-973` | Title of a notification-target message for a new message in a standard channel; the body is the message text and the channel link | None | Only standard channels send these (section 9.3) |
| `Event sink failed for {event_payload.event}` | Log line | `backend/open_webui/events.py:1197-1202` | Handing a channel event to one of the event destinations failed | None | Server log only; see section 8 and `notifications-webhooks-events-and-banners.md` |
| `Event webhook failed for {id}` | Log line | `backend/open_webui/events.py:1046-1059` | An admin event webhook could not be reached for a channel or message event | None | Server log only; which event webhooks production has is TO BE CONFIRMED (section 9.4) |
| `Notification delivery failed for user {user_id} and event {event.event}` | Log line | `backend/open_webui/utils/notifications.py:403-419` | Sending a `channel.message` notification-target message for one person failed | None | Server log only; section 11.5 |

### 10.2 Messages in the Screens

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` | Error (or Warning for the upload line) | `src/lib/components/layout/Sidebar.svelte:863`; `src/lib/components/layout/Sidebar/ChannelItem.svelte:222`; `src/lib/components/channel/Channel.svelte:257`; `src/lib/components/channel/Thread.svelte:155`; `src/lib/components/channel/Messages.svelte:146`, `:162`, `:187`, `:224`, `:250`; `src/lib/components/channel/PinnedMessagesModal.svelte:33`, `:121`; `src/lib/components/channel/ChannelInfoModal.svelte:48`; `src/lib/components/channel/ChannelInfoModal/UserList.svelte:68`; `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:28`; `src/lib/components/channel/WebhooksModal.svelte:55`, `:70`, `:83`; `src/lib/components/channel/MessageInput.svelte:486`, `:502` | The server's text (section 10.1) when creating a channel, hiding a direct message, posting, replying in a thread, deleting, editing, pinning, reacting, loading pins or members, adding or removing members, or managing webhooks; for uploads, the file service's text (`files-uploads-and-storage.md`) | Depends on the text | Ask for the exact wording and match it in 10.1. After a refused delete, edit, pin or reaction the screen already shows the change; a reload shows the true state (`src/lib/components/channel/Messages.svelte:141-254`) |
| `[object Object]` | Error | `src/lib/components/channel/WebhooksModal.svelte:70` (and any `{error}` pop-up above) | The server refused the input itself (HTTP 422) and sent a list of problems, which the screen prints as text; in this area mainly a refused webhook picture | Try another picture; otherwise report it | Ask what was being saved; escalate with the time |
| `Please select at least one user for Direct Message channel.` | Error | `src/lib/components/layout/Sidebar.svelte:843-847` | **Create** pressed for a **Direct Message** with nobody chosen | Choose at least one person | None |
| `Channel name cannot be empty.` | Error | `src/lib/components/layout/Sidebar.svelte:848-851` | **Create** pressed for a **Channel** or **Group Channel** whose name is empty or only spaces | Type a name | None |
| `Channel name must be less than 128 characters` | Error | `src/lib/components/layout/Sidebar/ChannelModal.svelte:57-63` | The name is longer than 128 characters | Shorten it | None |
| `Channel deleted successfully` | Success | `src/lib/components/layout/Sidebar/ChannelModal.svelte:116-127` | The channel was deleted from **Edit Channel**; the person is sent home if they were in it | None | Deletion is permanent (section 5.8) |
| `Are you sure you want to delete this channel?` | Confirmation (title `Confirm your action`) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:317-324`; `src/lib/components/common/ConfirmDialog.svelte:140-144` | **Delete** in **Edit Channel** | **Delete** to confirm | None |
| `Channel updated successfully` | Success | `src/lib/components/layout/Sidebar/ChannelItem.svelte:60-77` | **Update** in **Edit Channel** succeeded | None | The description and hidden details are cleared on save (section 5.8) |
| `Discussion channel where access is based on groups and permissions` | Notice (help text) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:206-207` | **Channel** chosen as the type (admins only) | None | Identifies a standard channel |
| `Collaboration channel where people join as members` | Notice (help text) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:208-209` | **Group Channel** chosen | None | Identifies a group channel |
| `Private conversation between selected users` | Notice (help text) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:210-211` | **Direct Message** chosen | None | Identifies a direct message |
| `A discussion channel where access is controlled by groups and permissions` | Notice (tooltip) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:174-182` | Hovering **Channel Type** while **Channel** is chosen | None | As above |
| `A collaboration channel where people join as members` | Notice (tooltip) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:174-182` | Hovering **Channel Type** while **Group Channel** is chosen | None | As above |
| `A private conversation between you and selected users` | Notice (tooltip) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:174-182` | Hovering **Channel Type** while **Direct Message** is chosen | None | As above |
| `You do not have permission to send messages in this channel.` | Notice (the message box is disabled) | `src/lib/components/channel/Channel.svelte:400-411` | The person can read this standard channel but has no write grant (`write_access` false) | Ask an admin for write access | Section 3.2; the message toolbar is hidden too (`src/lib/components/channel/Messages.svelte:134`) |
| `You do not have permission to send messages in this thread.` | Notice (the thread box is disabled) | `src/lib/components/channel/Thread.svelte:245-254` | As above, in the **Thread** panel | As above | As above |
| `This channel was created on {{createdAt}}. This is the very beginning of the {{channelName}} channel.` | Notice | `src/lib/components/channel/Messages.svelte:105-113` | Shown above the oldest message once all messages are loaded. For a direct message without a name the channel name is empty, so the sentence reads "the  channel" | None | `{{createdAt}}` is the creation date, for example "March 3, 2026" |
| `Start of the channel` | Notice | `src/lib/components/channel/Messages.svelte:115-118` | The same place when the channel's details are missing; the channel page shows its list only after the details load (`src/lib/components/channel/Channel.svelte:355`), so this is not normally reached | None | None |
| `Loading...` | Status | `src/lib/components/channel/Messages.svelte:61-74`; `src/lib/components/channel/PinnedMessagesModal.svelte:140-150` | Older messages (or more pins) are being fetched while scrolling | Wait | A spinner that never ends after a reload is an escalation |
| `Are you sure you want to delete this message?` | Confirmation (title **Delete Message**) | `src/lib/components/channel/Messages/Message.svelte:158-165` | **Delete** on a message | Confirm to delete | Deletion is permanent and leaves thread replies unreachable (section 5.7) |
| `Pinned` | Notice | `src/lib/components/channel/Messages/Message.svelte:307-314` | The message is pinned | None | Any writer can pin or unpin (section 3.2) |
| `Unknown User` | Notice | `src/lib/components/channel/Messages/Message.svelte:350-363` | A quoted message's sender has no name; when the sender's account no longer exists the quote line is not shown at all (`:316`) | None | None |
| `(edited)` | Notice | `src/lib/components/channel/Messages/Message.svelte:553-556` | The message was changed after posting (its two times differ); not shown on model replies | None | Pins and reactions do not change the time, so they do not mark a message edited (`backend/open_webui/models/messages.py:415-428`) |
| `{{NAMES}} reacted with {{REACTION}}` | Notice (tooltip) | `src/lib/components/channel/Messages/Message.svelte:560-597` | Hovering a reaction. Names are joined with `,` and `and`; the person sees `You` for themselves; above four people the rest is `and {{COUNT}} others` | None | With exactly four people the tooltip names only three (the fourth is dropped by `:569-592`); the count on the reaction is still right |
| `{{COUNT}} Replies` | Notice | `src/lib/components/channel/Messages/Message.svelte:641-662` | A top-level message has thread replies; followed by ` - ` `Last reply` and how long ago | Press it to open the thread | Thread replies never appear in the main list (section 4) |
| `Failed to read clipboard contents` | Error | `src/lib/components/channel/MessageInput.svelte:106-111` | A saved prompt containing `{{CLIPBOARD}}` was used and the browser refused clipboard access | Allow clipboard access for the site, or paste by hand | None |
| `Location access not allowed` | Error | `src/lib/components/channel/MessageInput.svelte:132-139` | A saved prompt containing `{{USER_LOCATION}}` was used and the browser refused location access; `LOCATION_UNKNOWN` is inserted instead | Allow location access, or edit the text | The location would be shared with everyone in the channel (section 5.5) |
| `File size should not exceed {{maxSize}} MB.` | Error | `src/lib/components/channel/MessageInput.svelte:364-378` | A file larger than the site's upload limit (`rag.file.max_size`) | Use a smaller file | The limit is a site setting (section 7.1) |
| `You cannot upload an empty file.` | Error | `src/lib/components/channel/MessageInput.svelte:454-457` | A zero-byte file | Choose the right file | None |
| `File not found.` | Error | `src/lib/components/channel/MessageInput.svelte:698-704` | The file picker closed without returning a file | Try again | None |
| `{names} is typing...` | Status | `src/lib/components/channel/MessageInput.svelte:754-768` | Someone else is typing in this channel or thread; `{names}` lists them, separated by commas | None | Cleared after 5 seconds without typing (section 4) |
| `Replying to {{NAME}}` | Status | `src/lib/components/channel/MessageInput.svelte:814-835` | **Reply** was pressed on a message | Escape or **×** cancels | None |
| `Permission denied when accessing microphone: {{error}}` | Error | `src/lib/components/channel/MessageInput.svelte:1026-1042` | Voice input pressed and the browser refused the microphone; `{{error}}` is the browser's reason | Allow the microphone for the site | See `audio-speech-to-text-and-text-to-speech.md` |
| `Permission denied when accessing microphone` | Error | `src/lib/components/channel/MessageInput.svelte:1050-1052` | As above, when the browser failed in another way | As above | As above |
| `No pinned messages` | Notice | `src/lib/components/channel/PinnedMessagesModal.svelte:100-104` | The channel has no pinned messages, or loading them failed after an error pop-up | None | None |
| `Member removed successfully` | Success | `src/lib/components/channel/ChannelInfoModal.svelte:44-58` | The creator removed a member of a group channel | None | The person's earlier messages stay (section 5.3) |
| `Failed to remove member` | Error | `src/lib/components/channel/ChannelInfoModal.svelte:55-57` | The server refused (after a pop-up with its text) or removed nobody, for example because the person had already been removed (`backend/open_webui/models/channels.py:494-508`) | Reopen the member list to see the current state | None |
| `No users were found.` | Notice | `src/lib/components/channel/ChannelInfoModal/UserList.svelte:282-286` | The member search matched nobody, or the list could not load | Change the search | None |
| `Members added successfully` | Success | `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:23-35` | **Add** in **Add Members** succeeded, including when everyone chosen was already a member | The new members reload their page to see the channel | Section 5.3 step 6 |
| `Failed to add members` | Error | `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:36-38` | The server refused (after a pop-up with its text) | As the earlier pop-up says | None |
| `Saved` | Success | `src/lib/components/channel/WebhooksModal.svelte:60-73` | **Save** in **Webhooks** stored the name and picture changes | None | The address does not change (section 5.9) |
| `Deleted` | Success | `src/lib/components/channel/WebhooksModal.svelte:75-85` | A webhook was deleted; its address stops working at once | None | Section 5.9 step 7 |
| `No webhooks yet` | Notice | `src/lib/components/channel/WebhooksModal.svelte:158-162` | The channel has no webhooks, or the list could not load (the error is not shown, `:34-41`) | None | If the person expected webhooks, escalate |
| `This action cannot be undone. Do you wish to continue?` | Confirmation (title `Confirm your action`) | `src/lib/components/channel/WebhooksModal.svelte:97`; `src/lib/components/common/ConfirmDialog.svelte:140-154` | **Delete** on a webhook | **Confirm** to delete | None |
| `Copied` | Success | `src/lib/components/channel/WebhookItem.svelte:73-78` | **Copy URL** on a webhook; shown without checking that the browser accepted the copy | Paste the address only into the outside system | The address is a secret (section 5.9) |
| `Active` | Status | `src/lib/components/channel/Messages/Message/UserStatus.svelte:51-62` | The person in a profile preview was active within the last three minutes | None | Section 8 (presence) |
| `Away` | Status | `src/lib/components/channel/Messages/Message/UserStatus.svelte:63-71` | Otherwise | None | As above |
| `Unknown` | Notice (shown as `@Unknown` or `#Unknown`) | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte:56-79`, `:115` | A model or channel mention that the viewer cannot see (not in their model list or channel list) | None | Section 4 |
| `This is a default user permission and will remain enabled.` | Notice (admin) | `src/lib/components/admin/Users/Groups/Permissions.svelte:1001-1007` | An admin turns **Channels** off in a group while the default permission is on | Turn it off under **Default permissions** instead | Section 3.1 |
| `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.` | Error | `src/lib/components/chat/Settings/Notifications.svelte:60-73` | **Browser Notifications** turned on while the browser blocks notifications for the site | Allow notifications in the browser's site settings, then turn it on again | Section 11.5 |
| `{user.name} (#{channel.name})` | Notice (pop-up title) | `src/routes/+layout.svelte:865-893` | A new message from someone else in a channel the person is not viewing; for a direct message only `{user.name}`; the text is the message | Click it to open the channel or thread | Section 9.2 |
| `{title} / {WEBUI_NAME}` | Notice (browser notification title) | `src/routes/+layout.svelte:868-878` | As above, in the person's last active tab, with **Browser Notifications** on; `{WEBUI_NAME}` is MedIT GPT by default | None | Section 9.2 |

### 10.3 Failures That Show No Message

| What the person sees | Why | Source |
|---|---|---|
| Opening a channel (or a link to one) lands on the home page | The channel could not be loaded: deleted, no access, Channels off, or a hidden direct message | `src/lib/components/channel/Channel.svelte:124-140` |
| **Update** or **Delete** in **Edit Channel** shows an empty red pop-up | These two screens print `error.message`, but the client throws the server's text itself, which has no `message` part; the dialog closes anyway | `src/lib/components/layout/Sidebar/ChannelItem.svelte:68-70`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:65-74`, `:116-118`; `src/lib/apis/channels/index.ts:333-345`, `:364-376` |
| A sent message stays faded | The server never confirmed it: the send was refused (a pop-up shows why) or the confirmation event did not reach this browser (section 11.4) | `src/lib/components/channel/Channel.svelte:228-266`; `src/lib/components/channel/Messages.svelte:134-135` |
| **Message** in a profile preview does nothing | Starting the direct message failed (for example Channels are off); the error goes only to the browser console. The button also appears in previews outside channels, such as the admin user list | `src/lib/components/channel/Messages/Message/UserStatus.svelte:19-32`, `:117-137`; `src/lib/components/admin/Users/UserList.svelte:35` |
| The **Thread** panel spins forever | Loading the thread failed; the error is not caught | `src/lib/components/channel/Thread.svelte:44-62`, `:205-240` |
| A message's attachments show a grey placeholder that never fills | Loading the message's attachments and output failed | `src/lib/components/channel/Messages/Message.svelte:140-151`, `:455-458` |
| A mentioned model never answers, or its reply stays a grey placeholder | The poster cannot use that model, the reply was refused by the chat endpoint's channel checks, or the pipeline failed before streaming; the reason is only in the server log | `backend/open_webui/routers/channels.py:1001-1005`, `:1131-1132`; `backend/open_webui/main.py:1309-1347`; `src/lib/components/channel/Messages/Message.svelte:543-544` |
| A hidden direct message comes back after a reload | Hiding failed (a pop-up shows why) but the row had already been removed from the sidebar | `src/lib/components/layout/Sidebar/ChannelItem.svelte:210-224` |

Message count for this section: 16 server messages (three of them log lines) and 52 screen
messages, 68 in all, plus the 8 silent failures above.

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes settings, permissions, membership, channels or messages. The
steps below use what the person can see, plus questions for an admin where a setting has to be
read. Never ask for, copy or paste a webhook address (section 5.9), and never copy channel message
text into a ticket; describe it instead (section 1).

### 11.1 "I can't see Channels in the sidebar"

**Symptom.** The left sidebar has no **Channels** section, or the **Channels** heading shows
nothing under it.

**Likely causes, in order.**

1. Channels are off for the whole site. The switch `channels.enable` is off by default; while it is
   off nobody sees the section, admins included (`backend/open_webui/config.py:2028`;
   `src/lib/components/layout/Sidebar.svelte:1330`).
2. The person does not have the `features.channels` permission. The default is on, but an admin
   may have turned the default off and granted it to chosen groups only (section 3.1;
   `src/lib/components/layout/Sidebar.svelte:1330`).
3. The page was loaded before the switch or the permission changed. The sidebar reads both when the
   page loads (`src/lib/components/layout/Sidebar.svelte:404-414`; `backend/open_webui/main.py:2356`).
4. The section is folded. Its open or closed state is remembered by each browser, and it starts
   closed in a browser that has never opened it (`src/lib/components/layout/Sidebar.svelte:125`,
   `:1331-1334`; `src/lib/components/layout/Sidebar/Section.svelte:27-31`, `:90-94`).
5. The person has no channels yet. Group channels and direct messages appear only after someone
   adds the person (section 11.2); standard channels only when the person holds a read grant
   (`backend/open_webui/models/channels.py:394-430`).

**Diagnostic steps.**

1. Ask whether colleagues see **Channels**. If nobody does, cause 1 is likely.
2. Ask the person to reload the page, then to click the **Channels** heading if it is there.
3. If only this person is affected, ask an admin to look at the person's groups and at
   **Admin Panel › Users › Groups › Default permissions › Features Permissions › Channels**
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:994-1008`).
4. If nobody sees it, ask an admin whether **Admin Settings › General › Features › Channels** is
   on (`src/lib/components/admin/Settings/General.svelte:342-348`).

**Resolution.** Reloading and unfolding the section are things the person can do. Turning Channels
on, or granting the permission, is an admin decision; whether MedIT GPT offers Channels at all is
**TO BE CONFIRMED** (section 14).

**Escalation.** Send the person's account (email address), whether colleagues see Channels, the
browser used and the time of the last reload.

### 11.2 "I can't find a channel someone invited me to"

**Symptom.** A colleague says they added the person to a channel, but it is not in the person's
sidebar.

**Likely causes, in order.**

1. The person was added after their page loaded. No live event is sent when members are added, so
   the channel appears only after a reload (section 5.3 step 6;
   `backend/open_webui/routers/channels.py:628-663`). There is also no invitation message of any kind.
2. It is a standard channel (admins create these). Access comes from its access list: the person
   sees it only with a read grant for themselves, one of their groups, or everyone
   (`backend/open_webui/models/channels.py:411-420`).
3. It is a group channel marked **Public**. "Public" changes only the icon; non-members still cannot
   see or open it (section 4; `backend/open_webui/models/channels.py:398-409`).
4. The colleague added a group, but the person joined that group later. Adding a group adds only its
   members at that moment (section 5.3 step 5; `backend/open_webui/models/channels.py:468-492`).
5. The **Channels** section is folded (section 11.1, cause 4).
6. It is a direct message the person hid with **×** (section 11.14).
7. The channel was deleted, or the person was removed from it; the old link now leads to the home
   page (`src/lib/components/channel/Channel.svelte:124-140`).

**Diagnostic steps.**

1. Ask for the channel's name and kind (channel, group channel or direct message) and who created it.
2. Ask the person to reload the page and unfold **Channels**.
3. For a group channel, ask the creator to open the member count in the channel's top bar and
   check that the person is listed (`src/lib/components/channel/Navbar.svelte:174-193`).
4. For a standard channel, ask the admin who manages it whether the person (or one of their groups)
   is on its access list.

**Resolution.** Guidance only: reload; the creator adds the person (group channel) or an admin
changes the access list (standard channel). A direct message can also be started from the
person's side (section 5.4).

**Escalation.** Send the channel's address if known (`/channels/{id}`), its kind, its creator and
the person's account.

### 11.3 "The model doesn't answer when I mention it"

**Symptom.** The person typed `@` and a model's name, posted, and no answer appeared.

**Likely causes, in order.**

1. The answer is in a thread. With **Model Response Mode** set to **Thread** (the default), the
   model answers in a thread under the message; the message then shows "1 Replies"
   (`backend/open_webui/routers/channels.py:1015-1021`;
   `src/lib/components/channel/Messages/Message.svelte:641-662`).
2. The model's name was typed rather than picked from the `@` list, so no mention was made
   (section 4; `backend/open_webui/utils/channels.py:4-10`).
3. The person cannot use that model. The server looks the model up in the poster's own model list
   and silently skips it otherwise (`backend/open_webui/routers/channels.py:977`, `:1001-1005`).
   The person's own direct-connection models are not offered at all
   (`src/lib/components/channel/MessageInput/MentionList.svelte:153-158`).
4. The mention was added by editing an earlier message. Only posting asks a model to answer
   (section 5.7).
5. The answer failed: the reply stays a grey placeholder or reads `Error: {error_content}`
   (section 10; `backend/open_webui/socket/main.py:1126-1129`;
   `backend/open_webui/routers/channels.py:1131-1132`).
6. The message came through an incoming webhook, which never makes models answer (section 5.9).

**Diagnostic steps.**

1. Ask the person to look for "Replies" under their message and open the thread.
2. Ask whether the mention looked highlighted in the posted message (a picked mention is shown as
   `@{model name}`; typed text is plain).
3. Ask whether the same model works in an ordinary chat. If it is not in their model selector there,
   cause 3 applies (`workspace-models-and-model-access.md`).
4. Ask the person to reload: a reply that streamed while the page was not receiving live updates
   shows after a reload (section 11.4, cause 3).

**Resolution.** Post again, choosing the model from the `@` list; open the thread; use a model the
person can access. Model access and the response mode are admin settings.

**Escalation.** Send the channel's address, the time of the message, the model's name, and any
`Error:` text shown in the reply.

### 11.4 "My message disappeared"

**Symptom.** A message the person posted is no longer in the channel, or it stays faded.

**Likely causes, in order.**

1. It was a thread reply. Thread replies appear only in the **Thread** panel, never in the main list
   (section 4).
2. The send failed. The faded copy stays until the page is reloaded and then vanishes, because the
   server never saved it; a pop-up with the reason appears unless the request got no reply at all
   (`src/lib/components/channel/Channel.svelte:228-266`; section 10.3).
3. The message was saved but this browser missed the confirmation, for example because the person
   was added to the channel after their page loaded. The faded copy then stays until a reload,
   which shows the saved message (`backend/open_webui/routers/channels.py:1171-1187`;
   `backend/open_webui/socket/main.py:479-484`).
4. Someone deleted it. The author or an admin can delete a message, permanently; a model's reply is
   stored under the person who mentioned the model, so that person can delete it too (sections 3.2
   and 5.7).
5. Its thread's first message was deleted, which leaves the replies unreachable (section 5.7).
6. The channel was deleted, or the person was removed from it (section 5.8).
7. It is older than the 50 messages loaded at first; scrolling up loads more
   (`src/lib/components/channel/Channel.svelte:124-141`).

**Diagnostic steps.**

1. Ask whether it was a reply in a thread, whether it looked faded, and whether a pop-up appeared
   (ask for its exact text).
2. Ask the person to reload the page and scroll up.
3. Ask a colleague in the same channel whether they see the message.

**Resolution.** Guidance only. A deleted message cannot be restored: there is no recycle bin
(`backend/open_webui/models/messages.py:588-596`).

**Escalation.** Send the channel's address and the approximate time. The database keeps no record
of who deleted a message (the row is removed); the `message.deleted` site event (section 9.4) and
the optional audit log are the only traces, and whether production keeps either is
**TO BE CONFIRMED**.

### 11.5 "Notifications don't arrive"

**Symptom.** The person expects to be told about new channel messages and is not. First establish
which kind is meant: the in-app pop-up, a browser (system) notification, or a message to their own
notification target. The application sends no email (ground truth).

**Likely causes, in order.**

1. They were looking at that channel in a visible tab, or the message was their own (including a
   model reply produced from their mention): no pop-up is shown by design (section 9.2).
2. Their browser is not receiving the channel's live updates, typically because they were added
   after their page loaded. A reload fixes it (sections 5.3 and 9.2).
3. Browser notifications: **Settings › Notifications › Browser Notifications** is off, the browser
   or operating system blocks notifications for the site, or the message arrived in a tab that was
   not their last active one (`src/routes/+layout.svelte:868-878`;
   `src/lib/components/chat/Settings/Notifications.svelte:60-73`).
4. Notification targets: these are sent only for **standard** channels, only to people who have
   opened that channel at least once, only when they had no live connection to it at the time, and
   only while the site's **User Webhooks** switch is on; webhook posts and model replies never send
   them (section 9.3).
5. They expected a mention to notify them specially; mentioning a person does nothing extra
   (section 4).
6. Delivery to a target failed on the server; the log line is
   `Notification delivery failed for user {user_id} and event {event.event}` (section 10.1).

**Diagnostic steps.**

1. Ask which kind of notification is missing, and in which channel (and its kind).
2. Ask the person to reload, then ask a colleague to post while the person is on a different page.
3. For browser notifications, ask them to check the setting and the browser's site permission
   (`Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.`
   appears when the browser blocks it).
4. For notification targets, check that the channel is a standard channel and that **Notification
   Targets** is visible to them in **Settings › Notifications** (section 9.3).

**Resolution.** Guidance on reloading and on browser and personal settings. The site's **User
Webhooks** switch and the `features.webhooks` permission are admin settings.

**Escalation.** Send the kind of notification, the channel's address, the time of a message that
was missed, the browser and, for targets, the target's type. Never include a target's address: it
may contain a secret.

### 11.6 "A webhook stopped posting"

**Symptom.** An outside system that posts into a channel through an incoming webhook no longer
does so.

**Likely causes, in order.**

1. Channels were turned off for the site; the system receives `Channels is disabled`
   (`backend/open_webui/routers/channels.py:2014`).
2. The webhook was deleted (by the channel's creator or an admin), or the system uses a wrong or
   outdated address; the system receives
   `The URL you provided is invalid. Please double-check and try again.`
   (`backend/open_webui/routers/channels.py:2016-2022`).
3. The channel was deleted. Depending on the database the webhook is removed with it (the system
   then receives the "invalid URL" text) or left behind (the system receives
   `We could not find what you're looking for :/`) (section 5.8 step 5;
   `backend/open_webui/routers/channels.py:2025-2026`).
4. The server could not save the message; the system receives
   `[ERROR: Failed to create message]` (`backend/open_webui/routers/channels.py:2036-2040`).
5. The posts arrive but people do not see them live; a reload shows them (section 11.4, cause 3).

**Diagnostic steps.**

1. Ask the system's owner for the status code and reply text their system received, and the time of
   the last post that worked. Do not ask for the address.
2. Ask the channel's creator (or an admin) to open **Edit Channel › Webhooks › Manage** and check
   that the webhook is still listed (`src/lib/components/channel/WebhooksModal.svelte:99-162`). The
   screens do not show when a webhook was last used; the `channel_webhook.last_used_at` column does
   (section 6.6).
3. Ask colleagues whether the channel still opens.

**Resolution.** The channel's creator or an admin makes a new webhook and hands its address to the
system's owner by a secure route; tier 1 never handles the address.

**Escalation.** Send the channel's address, the webhook's name, the status code and reply text,
and the time of the last successful post. A suspected leak of a webhook address is a security
matter: refer it to U of T Information Security (security.utoronto.ca).

### 11.7 "I can read the channel but I can't post"

**Symptom.** The message box is greyed out and reads
`You do not have permission to send messages in this channel.`, and the hover buttons on messages
are missing.

**Likely causes, in order.**

1. It is a standard channel and the person has read access but no write access (section 3.2;
   `src/lib/components/channel/Channel.svelte:408-411`).
2. Write access was removed after the page loaded; a reload shows the current state.

**Diagnostic steps.** Ask for the channel's address and confirm it is a standard channel (a `#` or
padlock icon, created by an admin). Ask whether colleagues can post there.

**Resolution.** Guidance only. An admin can add a **Write** entry for the person or a group, or
turn on **Allow public write access** (`src/lib/components/workspace/common/AccessControl.svelte:517-560`).

**Escalation.** Send the channel's address and the person's account.

### 11.8 "Channels disappeared from my sidebar but I still get channel pop-ups"

**Symptom.** After Channels were withdrawn from the person, pop-ups for channel messages still
appear.

**Likely causes.** The live-update room check does not read the saved default permissions in the
same way as the rest of the server (section 3.1).

**Diagnostic steps.** Confirm only the time the pop-ups were seen and the person's account. Do not
collect message text.

**Resolution.** None at tier 1.

**Escalation.** Security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca).

### 11.9 "Opening the channel takes me back to the home page"

**Symptom.** Clicking a channel, a channel link or a pop-up lands on the home page with no message
(`src/lib/components/channel/Channel.svelte:124-140`).

**Likely causes, in order.**

1. The channel was deleted (section 5.8).
2. The person was removed from the group channel, or lost their grant on the standard channel.
3. It is a direct message the person hid; while hidden it cannot be opened (section 5.4 step 6).
4. Channels were turned off, or the person's permission was withdrawn (section 11.1).

**Diagnostic steps.** Ask whether colleagues can still open it and who created it; ask the person
to reload so the sidebar list is current.

**Resolution.** Guidance only; for a hidden direct message, start a direct message with the same
people again (section 5.4).

**Escalation.** Send the channel's address, its creator and the time.

### 11.10 "I can't add or remove people"

**Symptom.** The member list has no **Add Member** button or **×** buttons.

**Likely causes, in order.**

1. The person did not create the channel. Only the creator gets these buttons, even for admins
   (section 3.3; `src/lib/components/channel/ChannelInfoModal.svelte:117-128`).
2. It is a direct message: the screens offer no way to add or remove its members; a new direct
   message with the new set of people is the way (section 5.4 step 7).
3. It is a standard channel: membership comes from the access list in **Edit Channel**, not from
   the member list (section 4).

**Diagnostic steps.** Ask for the channel's kind and who created it.

**Resolution.** Guidance: ask the creator, or for a standard channel the admin who manages it.

**Escalation.** Only if the creator's account no longer exists and the channel still needs a
manager; send the channel's address (whether admins should act on such channels is
**TO BE CONFIRMED**, section 14).

### 11.11 "Saving or deleting the channel shows an empty red box"

**Symptom.** **Update** or **Delete** in **Edit Channel** shows a red pop-up with no words, and
the dialog closes.

**Likely causes, in order.**

1. The server refused the change (the person is neither the creator nor an admin, Channels were
   turned off, or the permission was withdrawn), or it failed. These two buttons cannot show the
   server's text (section 10.3).

**Diagnostic steps.** Ask the person to reload and reopen **Edit Channel** to see whether the
change was saved; ask whether other channel actions show `Channels is disabled` or another text.

**Resolution.** Guidance only.

**Escalation.** Send the channel's address, the action and the time.

### 11.12 "How do I leave a channel?"

**Symptom.** The person wants a channel out of their list.

**Likely causes.** There is no "leave" action in this version (section 3.2).

**Diagnostic steps.** Ask which kind of channel it is.

**Resolution.** A direct message can be hidden with **×** on its sidebar row (section 5.4). For a
group channel, the creator removes the person (section 5.3 step 7). For a standard channel, the
admin who manages it changes the access list; the membership row created when the person first
opened it stays (section 4).

**Escalation.** None normally.

### 11.13 "The unread count is wrong"

**Symptom.** The number beside a channel does not match what the person sees.

**Likely causes, in order.**

1. While the page is open, thread replies also raise the count, but after a reload only top-level
   messages count, so the number can fall (section 5.10 step 4).
2. The channel was added after the page loaded, so reading it is not recorded until a reload
   (section 5.10 step 2).
3. A standard channel the person has never opened shows no count (section 5.10 step 3).
4. The person's own messages, and webhook posts in channels whose webhooks the person created, are
   never counted (`backend/open_webui/models/messages.py:430-446`; section 6.3).

**Diagnostic steps.** Ask the person to open the channel, then reload.

**Resolution.** Opening the channel resets the count.

**Escalation.** Only if the count stays wrong after opening the channel and reloading.

### 11.14 "A direct message vanished from my sidebar"

**Symptom.** A direct message is no longer listed.

**Likely causes, in order.**

1. The person pressed **×** on its row, which hides it for them only; nothing is deleted
   (section 5.4 step 5).

A related report is a direct message row with no name or picture. That happens when the other
person's account was deleted: account deletion does not remove channel memberships
(`backend/open_webui/models/users.py:849-863`), and the row lists only people whose accounts still exist
(`backend/open_webui/routers/channels.py:193-205`;
`src/lib/components/layout/Sidebar/ChannelItem.svelte:115-172`). Matching also counts only
existing accounts, so starting a direct message with the remaining people of a larger conversation
reopens that conversation, earlier messages included (`backend/open_webui/models/channels.py:432-466`).

**Diagnostic steps.** Ask whether they hid it, and who was in it.

**Resolution.** It comes back when anyone posts in it, or when the person starts a direct message
with exactly the same people (section 5.4 step 6).

**Escalation.** None normally.

### 11.15 "Colleagues get an empty pop-up with my name when I mention a model"

**Symptom.** Others report pop-ups that show the person's name and no text.

**Likely causes.** A model's reply starts as an empty message stored under the person who mentioned
the model; the answer then arrives as updates, which raise no pop-up (section 9.2).

**Diagnostic steps.** None needed.

**Resolution.** Explain that this is how this version works.

**Escalation.** None.

## 12. Local Customisations

Compared with upstream v0.11.4 (`git diff main...uoft`), the fork changes **two files** in this
area, both in the front end. No backend file in scope (`backend/open_webui/routers/channels.py`,
`backend/open_webui/models/channels.py`, `backend/open_webui/models/messages.py`,
`backend/open_webui/utils/channels.py`, `backend/open_webui/socket/main.py`, the `channels.*`
keys in `backend/open_webui/config.py`) and no API client file differs, and there is no
fork-specific migration (ground truth). Everything else in this document is upstream behaviour.

### 12.1 Browser Tab Title Uses the App Name

| What | Upstream | Fork | Source |
|---|---|---|---|
| Tab title of a channel page | `#{channel name} / Open WebUI` | `#{channel name} / {WEBUI_NAME}`, so `#{channel name} / MedIT GPT` with the fork's default name | `src/lib/components/channel/Channel.svelte:313-335`; commit `402a737ba` |
| Tab title of a direct message | `{name, or the other people's names} / Open WebUI` | `{name, or the other people's names} / {WEBUI_NAME}` | `src/lib/components/channel/Channel.svelte:317-331` |

- `{WEBUI_NAME}` is the app-name store (`src/lib/stores/index.ts:14`), filled from the server's
  configuration when the page loads (`src/routes/+layout.svelte:1274`); the server's name comes from
  the environment variable `WEBUI_NAME`, default `MedIT GPT` (ground truth). The production value
  is **TO BE CONFIRMED** (ground truth).
- The licence comment above the title (`src/lib/components/channel/Channel.svelte:314-316`) is kept;
  the maintainer has confirmed a LICENSE §4 branding exception, and which exception applies is
  **TO BE CONFIRMED** (ground truth; `CLAUDE.md`).
- Browser notifications for channel messages already used the app name upstream
  (`src/routes/+layout.svelte:873`); only the default name changed (section 9.2).

### 12.2 Hide Processing Details Also Applies to Model Replies in Channels

| What | Upstream | Fork | Source |
|---|---|---|---|
| Deciding whether a model reply is drawn as structured output | All processing steps counted | Steps are counted only as the person's **Hide Processing Details** setting allows | `src/lib/components/channel/Messages/Message.svelte:153-155`; commit `aeed1832c` |

- **Hide Processing Details** is the fork's per-person setting in **Settings › Interface** (label
  "Hide Processing Details", `src/lib/i18n/locales/en-US/translation.json:2924`; description at
  `:2923`; model field `backend/open_webui/models/users.py:99-100`). Its full behaviour is in
  `chat-composer-and-message-display.md`.
- Effect in a channel: with the setting on, status lines, reasoning and code-analysis steps are left
  out of model replies, and tool-call cards are hidden (`src/lib/components/chat/Messages/structuredOutput.ts:344-447`;
  `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:70-71`;
  `src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`, `:199`). While a reply has
  produced only such steps, the person sees the grey loading placeholder instead of the steps
  (`src/lib/components/channel/Messages/Message.svelte:536-544`). Channel replies run tools with
  **Full access**, so no approval requests appear there (section 3.5), and channels do not show
  embeds (`allowEmbeds={false}`, `src/lib/components/channel/Messages/Message.svelte:537-541`).
- The setting changes only what this person sees; other members see the reply according to their
  own setting. The stored reply is the same for everyone (`backend/open_webui/socket/main.py:1033-1067`).

### 12.3 Fork Pictures Seen in Channels

The fork replaced the default pictures (ground truth). In channels they appear as the fallback
picture of a webhook that has none, whose picture is a web address while
`ENABLE_PROFILE_IMAGE_URL_FORWARDING` is off, or that no longer exists
(`backend/open_webui/routers/channels.py:1828-1833`, `:1870-1874`, serving
`backend/open_webui/static/favicon.png`), and as the fallback when a model's
picture fails to load (`src/lib/components/channel/Messages/Message.svelte:383-392`, loading
`static/favicon.png`). The file contents differ from upstream; the code does not.

### 12.4 Uncommitted Working-Tree Changes That Reach Channels

No file in this area's scope has uncommitted changes (`git diff` on the scope paths is empty).
Channel messages do, however, use shared chat components that do:

| Shared file | Used in channels for | Change, as far as the code shows | Source |
|---|---|---|---|
| `src/lib/components/chat/Messages/structuredOutput.ts` | Model reply output (`buildOutputDisplayItems`) | With **Hide Processing Details** on, tool calls are kept one by one and other steps dropped, written more simply; a new helper `hasPendingToolCall` is added | `src/lib/components/chat/Messages/structuredOutput.ts:404-416`, `:454-457` |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | Drawing model reply output | No longer passes the setting to the tool-call display, which now reads it itself | `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:176-186`; `src/lib/components/common/ToolCallDisplay.svelte:145` |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte`, `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Drawing every channel message's Markdown (`src/lib/components/channel/Messages/Message.svelte:545-552`) | The same hiding rules, restructured; status lines are hidden when the setting is on | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:90-104`; `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-105` |
| `src/lib/i18n/index.ts` | All screen text | Language detection maps a browser language to an available translation, and `en-US` becomes the last fallback when a site default language is set | `src/lib/i18n/index.ts:77-86`, `:93` |

Whether these working-tree changes are deployed is **TO BE CONFIRMED** (section 14).

## 13. Source File Index

Line counts are from the working tree on 2026-10-10. "Read" means the file was opened for this
document; "cited" means only the lines cited were checked.

### 13.1 Backend, in Scope

| File | Lines | Role in this area | Read |
|---|---|---|---|
| `backend/open_webui/routers/channels.py` | 2,084 | Every channel endpoint under `/api/v1/channels`: the site and permission gate, lists, direct-message lookup, create, members, update, delete, messages, pins, threads, reactions, webhooks and the incoming webhook address; the model-reply and notification-target background work | Read in full |
| `backend/open_webui/models/channels.py` | 1,009 | Tables `channel`, `channel_member`, `channel_file`, `channel_webhook`; channel lists, direct-message matching, membership, manager check, update and delete | Read in full except the webhook helpers, which were cited |
| `backend/open_webui/models/messages.py` | 625 | Tables `message` and `message_reaction`; webhook sender names, threads, pins, unread counts, reactions, deletion, message search | Read in full |
| `backend/open_webui/utils/channels.py` | 31 | Mention tokens: `extract_mentions`, `replace_mentions` | Read in full |
| `backend/open_webui/socket/main.py` | 1,289 | Channel rooms (`user-join`, `join-channels`), the `events:channel` handler (typing, read position), room helpers, and the channel emitter that streams model replies (`:1019-1131`) | Channel parts read (`:60-115`, `:330-390`, `:440-581`, `:1000-1140`) |
| `backend/open_webui/config.py` | — | `USER_PERMISSIONS_FEATURES_CHANNELS` `:1922`; `DEFAULT_USER_PERMISSIONS` `:1940-2022` (`channels` at `:2006`); `ENABLE_CHANNELS` `:2028`; `CHANNEL_MODEL_RESPONSE_MODE` `:2030`; `channels.enable`, `channels.model_response_mode` `:3104-3105` | Cited lines |

### 13.2 Backend, Related

| File | Role in this area | Read |
|---|---|---|
| `backend/open_webui/models/access_grants.py` | Channel access grants: conversion, `set_access_grants` (`:443-478`), `has_access` (`:562-618`), `get_users_with_access` (`:678-721`), list filtering (`:723-800`) | Read `:1-190`, `:276-520`, `:676-725` |
| `backend/open_webui/utils/access_control/__init__.py` | `has_permission` (`:75-108`), `filter_allowed_access_grants` (`:223-300`) | Read those functions |
| `backend/open_webui/main.py` | Router mount `:860`; tool approval mode for channel replies `:1255-1263`; channel checks on model replies `:1309-1347`; `enable_channels` in `/api/config` `:2356` | Cited lines; `:1245-1360` read |
| `backend/open_webui/routers/auths.py` | Admin settings read and save for `channels.*` `:125-126`, `:1269-1296` | Cited lines |
| `backend/open_webui/events.py` | Channel and message event definitions `:215-285`; delivery to event webhooks, notification targets and Event functions `:1040-1202` | Read those ranges |
| `backend/open_webui/utils/notifications.py` | Notification-target text for `channel.message` `:307-322`; delivery `:393-419` | Read those ranges |
| `backend/open_webui/constants.py` | Error texts `:16-41`, `:69`, `:78`, `:99`, `:125` | Read those lines |
| `backend/open_webui/utils/validate.py` | Webhook picture validation `:35-96` | Read `:1-120` |
| `backend/open_webui/env.py` | `STATIC_DIR` `:252`; `ENABLE_PROFILE_IMAGE_URL_FORWARDING` `:970`; `PROFILE_IMAGE_ALLOWED_MIME_TYPES` `:971-977`; `PROFILE_IMAGE_MAX_DATA_URI_SIZE` `:982-983` | Cited lines |
| `backend/open_webui/models/users.py` | Deleting an account leaves channel memberships `:849-863`; presence `:911-916`; member filter by channel `:553-575` | Cited lines |
| `backend/open_webui/routers/automations.py`, `backend/open_webui/utils/automations.py` | Channel automations and the model defaults used for channel replies | Cited lines (see `automations-calendar-and-timers.md`) |
| `backend/open_webui/routers/files.py`, `backend/open_webui/utils/access_control/files.py` | Uploading files into a channel; channel readers opening channel files | Cited lines (see `files-uploads-and-storage.md`) |
| `backend/open_webui/tools/builtin.py` | Channel tools for models: `search_channels` `:1763`, `search_channel_messages` `:1815`, `view_channel_message` `:1896`, `view_channel_thread` `:1957`; automation target `:3788-3792` | Cited lines (see `builtin-native-tools.md`) |
| `backend/open_webui/migrations/versions/57c599a3cb57_add_channel_table.py`, `3781e22d8b01_update_message_table.py`, `6283dc0e4d8d_add_channel_file_table.py`, `81cc2ce44d79_update_channel_file_and_knowledge_table.py`, `90ef40d4714e_update_channel_and_channel_members_table.py`, `2f1211949ecc_update_message_and_channel_member_table.py`, `f1e2d3c4b5a6_add_access_grant_table.py` | Schema history (section 6.7) | Cited lines |
| `backend/open_webui/static/favicon.png` | Fallback webhook picture; replaced by the fork (section 12.3) | Existence and diff only |

### 13.3 Front End, in Scope

| File | Lines | Role in this area | Read |
|---|---|---|---|
| `src/routes/(app)/channels/[id]/+page.svelte` | 7 | The `/channels/{id}` route | Read in full |
| `src/lib/components/channel/Channel.svelte` | 468 | Channel page: loading, live events, posting, typing, read position, thread panel; fork tab title | Read in full |
| `src/lib/components/channel/Navbar.svelte` | 198 | Top bar: **Pinned Messages**, member count | Script read; cited lines |
| `src/lib/components/channel/Messages.svelte` | 261 | Message list, start-of-channel text, delete, edit, pin and reaction actions | Read in full |
| `src/lib/components/channel/Messages/Message.svelte` | 729 | One message: toolbar, quote, pin label, attachments, model output, reactions, reply count; fork setting | Read `:1-157`, `:158-664` in parts |
| `src/lib/components/channel/Messages/Message/ProfilePreview.svelte` | 60 | Profile preview wrapper | Read in full |
| `src/lib/components/channel/Messages/Message/UserStatus.svelte` | 139 | Presence and the **Message** button | Read `:1-75`, `:110-139` |
| `src/lib/components/channel/Messages/Message/UserStatusLinkPreview.svelte` | 52 | Loads the person shown in a preview | Read `:1-30` |
| `src/lib/components/channel/MessageInput.svelte` | 1,134 | The message box: prompts, variables, uploads, image compression, typing list, reply bar, voice | Messages and upload code read |
| `src/lib/components/channel/MessageInput/InputMenu.svelte` | 73 | **More** menu: **Upload Files**, **Capture** | Strings only |
| `src/lib/components/channel/MessageInput/MentionList.svelte` | 271 | `@` and `#` suggestions | Strings only; cited lines |
| `src/lib/components/channel/Thread.svelte` | 264 | **Thread** panel | Read in full |
| `src/lib/components/channel/PinnedMessagesModal.svelte` | 162 | **Pinned Messages** window | Read `:1-70`, `:95-150` |
| `src/lib/components/channel/ChannelInfoModal.svelte` | 138 | Channel information and member list window | Read `:1-70`, `:100-138` |
| `src/lib/components/channel/ChannelInfoModal/UserList.svelte` | 288 | Member list, search, remove buttons | Read `:40-100`, `:255-288` |
| `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte` | 106 | **Add Members** window | Read `:1-70` |
| `src/lib/components/channel/WebhooksModal.svelte` | 184 | **Webhooks** window | Read `:1-100`; strings |
| `src/lib/components/channel/WebhookItem.svelte` | 175 | One webhook: picture, name, **Copy URL**, **Delete** | Read `:1-125` |
| `src/lib/components/layout/Sidebar/ChannelItem.svelte` | 245 | Sidebar row, gear and **×** buttons, **Edit Channel** save | Read in full |
| `src/lib/components/layout/Sidebar/ChannelModal.svelte` | 326 | **Create Channel** and **Edit Channel** dialog | Read in full |
| `src/lib/apis/channels/index.ts` | 921 | Browser client for every channel endpoint | `:1-140` read; error handling of every function checked |

### 13.4 Front End, Related

| File | Role in this area | Read |
|---|---|---|
| `src/lib/components/layout/Sidebar.svelte` | **Channels** section, channel list loading, create handler | `:355-415`, `:835-880`, `:1325-1365` |
| `src/lib/components/layout/Sidebar/Section.svelte` | Folding sidebar sections, remembered per browser | `:12-40`, `:85-100` |
| `src/routes/+layout.svelte` | Socket connection and `user-join` (`:184-245`); channel pop-ups, browser notifications and unread counts (`:789-893`); app name (`:1274`) | Those ranges |
| `src/lib/stores/index.ts` | `WEBUI_NAME` `:14`, `channels` `:58`, `channelId` `:59` | Cited lines |
| `src/lib/components/admin/Settings/General.svelte` | Admin **Channels** switch and **Model Response Mode** | `:340-365` |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | **Channels** permission switch | `:990-1010` |
| `src/lib/components/chat/Settings/Notifications.svelte` | **Browser Notifications** and **Notification Targets** | `:60-78`; cited lines |
| `src/lib/components/NotificationToast.svelte` | In-app pop-up and its sound | `:68-84` cited |
| `src/lib/components/common/ConfirmDialog.svelte` | Default confirmation title and text | `:18-30`, `:136-158` |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte` | How mentions are shown and opened | `:40-125` |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte`, `src/lib/components/chat/Messages/structuredOutput.ts`, `src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte`, `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Drawing model replies and Markdown in channel messages (section 12) | Working-tree diffs and cited lines |
| `src/lib/components/workspace/common/AccessControl.svelte`, `Visibility.svelte`, `MemberSelector.svelte` | Access panel, group-channel visibility, people picker | Cited lines (see `users-groups-roles-and-permissions.md`) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted settings keys used here | Cited lines |
| `src/lib/i18n/index.ts` | Translation loading (working-tree change, section 12.4) | Working-tree diff |

## 14. Open Questions

Every **TO BE CONFIRMED** item in this document is gathered here, with the section that raises it.

### 14.1 Production Facts and Settings (TO BE CONFIRMED)

| # | Question | Raised in | Why the code cannot answer it |
|---|---|---|---|
| 1 | Is `channels.enable` on in production, and does MedIT GPT intend to offer Channels at all? | Sections 1, 11.1 | A stored setting (data) and a service decision |
| 2 | The production host name | Section 2 | Not in the repository (ground truth) |
| 3 | Live values of every setting in section 7: `channels.model_response_mode`, the saved **Default permissions** for `features.channels`, group grants, `ui.enable_user_webhooks`, `webui.url`, upload limits, and the environment-only `USER_PERMISSIONS_FEATURES_CHANNELS`, `ENABLE_PROFILE_IMAGE_URL_FORWARDING`, `PROFILE_IMAGE_MAX_DATA_URI_SIZE` and `PROFILE_IMAGE_ALLOWED_MIME_TYPES` | Sections 7, 10.1, 11 | Data in the `config` table or the environment |
| 4 | Which database production uses (SQLite or PostgreSQL). This also decides whether deleting a channel removes its webhooks and file links | Sections 5.8, 6, 11.6 | Ground truth: production stores are not in the repository |
| 5 | Whether production runs more than one server process, and if so how notification targets and new direct-message rooms behave; to be tested on the production layout | Section 8 | Depends on the deployment (ground truth) |
| 6 | Which admin event webhooks and Event functions production has, and whether they may receive channel text (`content_preview`) | Sections 9.4, 10.1 | Data |
| 7 | Whether production keeps any trace of who deleted a message: the `message.deleted` site event at a configured destination, or the optional audit log (`AUDIT_LOG_LEVEL`) | Section 11.4 | Data and deployment |
| 8 | Whether admins should act on a group channel whose creator's account no longer exists (no one else is its manager) | Section 11.10 | A service decision |
| 9 | The production value of `WEBUI_NAME` (the tab and notification titles) | Section 12.1 | Environment (ground truth) |
| 10 | Which LICENSE §4 branding exception applies | Section 12.1 | Not recorded in the repository (ground truth) |
| 11 | Whether the uncommitted working-tree changes in shared chat components (section 12.4) are deployed | Section 12.4 | Deployment practice is not in the repository |
| 12 | Where tier 1 sends the escalations listed in section 11 (team, queue, hours) | Section 11 | No support contact exists in the repository (ground truth) |
| 13 | Which model providers production uses for models people can mention in channels, since a mention sends the thread's names and words to that provider | Section 5.6 step 7 | Data (`model-connections-openai-ollama-and-direct.md`) |

### 14.2 Security-Sensitive Items (Referred Without Detail)

- The live-update room check for Channels does not read the saved default permissions in the same
  way as the server endpoints (section 3.1, correction of 2026-10-10; section 11.8).
  Security-sensitive: refer to the platform maintainer and U of T Information Security
  (security.utoronto.ca).
- Incoming webhook addresses carry their own secret (section 5.9). Handling of a suspected leak is
  a security matter for U of T Information Security; no further detail is recorded here.

### 14.3 Policy Questions for the Privacy Office (privacy.utoronto.ca)

- Whether admins may read or change private conversations, and how such access is recorded
  (section 3.4).
- Whether channel content left in the database after a channel or message is deleted (section 5.7
  step 3, section 5.8 step 5) meets U of T retention expectations, and how backups are treated.
- Whether people should be told that mentioning a model sends the thread's names and words to the
  model's provider, and that saved prompts with variables such as `{{USER_EMAIL}}` or
  `{{USER_LOCATION}}` share those values with the channel (sections 5.5 and 5.6).

### 14.4 Behaviours That Look Like Upstream Defects

These are what the code does in v0.11.4; none is a fork change. Whether to report them upstream or
patch them is for the maintainer.

| Behaviour | Source |
|---|---|
| **Update** and **Delete** in **Edit Channel** show an empty error pop-up, because they print `error.message` | `src/lib/components/layout/Sidebar/ChannelItem.svelte:68-70`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:116-118` |
| Webhook posts show the sender `Webhook` in **Pinned Messages** instead of the webhook's name | `backend/open_webui/routers/channels.py:910-917`, `:2028-2030` |
| With exactly four people on a reaction, the tooltip names only three | `src/lib/components/channel/Messages/Message.svelte:569-592` |
| A refused webhook picture shows `[object Object]` | `src/lib/components/channel/WebhooksModal.svelte:70` |
| `Copied` appears even if the browser refused the copy | `src/lib/components/channel/WebhookItem.svelte:73-78` |
| Removing a member who was already removed shows `Failed to remove member` | `src/lib/components/channel/ChannelInfoModal.svelte:44-58` |
| Saving from **Edit Channel** clears the channel's description and spare details (already noted in section 5.8) | `backend/open_webui/models/channels.py:830-851` |

### 14.5 Corrections, Verifications and Notes on Ground Truth

- **Verified 2026-10-10 (no change needed):** section 9.3's finding that no notification-target
  messages are sent for group channels or direct messages. The screens send an empty access list
  for these kinds (`src/lib/components/layout/Sidebar/ChannelModal.svelte:69`), the direct-message
  shortcut sends none (`backend/open_webui/routers/channels.py:263-271`),
  `filter_allowed_access_grants` returns an empty list unchanged
  (`backend/open_webui/utils/access_control/__init__.py:236-237`), and `set_access_grants`
  normalizes an empty or missing list to no rows; unlike the older `access_control_to_grants`, it
  never turns a missing list into public read (`backend/open_webui/models/access_grants.py:150-158`,
  `:443-478`, compare `:100-112`). `get_users_with_access` therefore returns nobody for these
  channels (`:678-721`). Only a group channel or direct message created through the API with
  explicit grants would behave differently.
- **Corrected 2026-10-10:** section 3.1 (the live-update room check) and section 9.2 step 1 (a
  visible tab, not a visible and focused one). Both corrections are marked in place.
- **Refinement to ground truth (time units):** ground truth lists `models/channels.py` among the
  models that store nanoseconds. That holds for channels, members and webhooks, but `channel_file`
  stores **seconds** (`backend/open_webui/models/channels.py:854-865`), as section 6 already says.
- **Refinement to ground truth (permissions):** "otherwise the default decides" means the saved
  default permissions when the caller passes them, but the environment-derived code defaults when
  it does not (`backend/open_webui/utils/access_control/__init__.py:75-108`); the channel socket
  checks are such a caller (section 3.1).

### 14.6 Not Established From the Code

- How the pop-up library draws an error pop-up with no text (section 10.3); the document says
  "empty red pop-up" from reading the code, not from a test in a browser.
- Whether production browsers keep the live connection on WebSocket or fall back to polling, which
  affects how quickly channel updates arrive (`websockets-realtime-and-redis.md`).
- The real-world wording of provider errors that end up in `Error: {error_content}` replies; it
  comes from the model provider, not from this code.
