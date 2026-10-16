# Users, Groups, Roles and Permissions

## At a Glance

- **Three roles: `admin`, `user` and `pending`.** The role is read from the database on every
  request, so a role change applies to the user's next request
  (`backend/open_webui/utils/auth.py:455`, `:567-576`). Any role other than `user` or `admin` gets
  the "Account Activation Pending" screen (`src/routes/(app)/+layout.svelte:445-446`).
- **Where admins work:** Admin Panel › Users › **Overview** (`/admin/users/overview`) for people and
  **Groups** (`/admin/users/groups`) for groups and default permissions
  (`src/lib/components/admin/Users.svelte:89-133`). The default role and default group for new
  accounts are on Admin Settings › Authentication (`/admin/settings/authentication`).
- **Approving a pending user means changing their role to `user`** in the Edit User dialog. Nothing
  notifies the person: no email exists and no in-app notification is sent; they click **Check
  Again** or reload (`src/lib/components/layout/Overlay/AccountPending.svelte:59-67`).
- **The primary admin is the earliest-created account.** Other admins cannot edit it, it cannot
  lose the `admin` role, and it cannot be deleted; no admin can delete their own account
  (`backend/open_webui/routers/users.py:923-949`, `:1046-1084`).
- **Deleting a user is permanent and partial.** The code removes group memberships, the user's
  chats (with their messages and share snapshots), the `user` row and the `auth` row; files,
  knowledge bases, models, prompts, tools, notes, memories, folders and other owned content stay
  behind with no new owner (`backend/open_webui/models/users.py:849-863`;
  `backend/open_webui/models/auths.py:228-239`).
- **Bulk import:** Add User › CSV Import takes a header row and then `Name,Email,Password,Role`
  rows; a group's Users tab imports `Name,Email` rows for accounts that already exist
  (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:65-134`;
  `src/lib/components/admin/Users/Groups/Users.svelte:65-84`).
- **65 permission keys in six sections** (`workspace`, `sharing`, `access_grants`, `chat`,
  `features`, `settings`). Code defaults come from `USER_PERMISSIONS_*` environment variables
  (`backend/open_webui/config.py:1733-2022`); after first boot the stored `user.permissions`
  setting wins.
- **Permissions only add up.** A user has a permission if the defaults or any of their groups
  grant it; a group cannot take away a default (`backend/open_webui/utils/access_control/__init__.py:75-108`).
  A new group starts with a **copy** of the current defaults, so later tightening of the defaults
  does not reach that group's members until the group is edited
  (`src/lib/components/admin/Users/Groups.svelte:113-121`).
- **Sharing uses access grants**: Read or Write for named users, groups, all users ("Public") and,
  for shared chats only, anyone with the link ("Open"). Grants the sharer is not allowed to make
  are dropped on save without an error (`backend/open_webui/utils/access_control/__init__.py:223-301`).
- **Admin visibility defaults (environment only, live values TO BE CONFIRMED):** admins can open
  users' chats (`ENABLE_ADMIN_CHAT_ACCESS`, on) and see every workspace item
  (`BYPASS_ADMIN_ACCESS_CONTROL`, on); model access control applies to non-admins unless
  `BYPASS_MODEL_ACCESS_CONTROL` is on (off), and to admins as well while
  `BYPASS_ADMIN_ACCESS_CONTROL` is off (section 3.7).
- **Privacy:** any signed-in `user` or `admin` can search all accounts by name or email fragment
  and see names, emails, roles and bios (`backend/open_webui/routers/users.py:137-161`). This is
  how share pickers find people.
- **"Active" means activity in the last 3 minutes** (`backend/open_webui/models/users.py:901-925`).
- **Fork status:** this area matches upstream Open WebUI v0.11.4 except that the fork's two
  Interface settings are among the fields the `settings.interface` permission protects (section 12).
- Tier 1 is read-only: diagnose and escalate; never change roles, groups, permissions or shares.

## 1. Purpose and Who Uses It

This area covers what happens to an account **after** it exists: which role it has, which groups
it belongs to, which features it may use, and which shared items it can reach. Signing in, sign-up,
passwords, LDAP and API keys are in `authentication-and-sign-in.md`; single sign-on, role and group
mapping from an identity provider, trusted headers and SCIM are in `sso-oauth-oidc-and-scim.md`.

Who uses it, as coded:

- **Administrators** (role `admin`) manage accounts on Admin Panel › Users: approve pending
  accounts, change roles, edit and delete users, add users one at a time or from a CSV file, view a
  user's chats, and preview what a user can reach
  (`src/lib/components/admin/Users/UserList.svelte:136-545`). On the Groups tab they create groups,
  manage members, set each group's permissions and share setting, and edit the **Default
  permissions** that apply to every `user` (`src/lib/components/admin/Users/Groups.svelte:112-247`).
- **Every signed-in user** meets this area through the share dialogs on models, knowledge bases,
  prompts, tools, skills, notes, folders, channels and shared chats, which list people and groups to
  share with (`src/lib/components/workspace/common/AccessControl.svelte:470-705`), and through
  features that appear or disappear according to their permissions (section 7.5).
- **Pending users** can sign in but see only the "Account Activation Pending" screen until an admin
  changes their role (`src/routes/(app)/+layout.svelte:445-446`;
  `src/lib/components/layout/Overlay/AccountPending.svelte:31-80`).
- **Tier-1 support** uses this document to explain why a feature, model or shared item is or is not
  available to someone, and to collect the right details before escalating. Tier 1 does not change
  roles, groups, permissions or shares.

The backend for this area is the users router (`/api/v1/users`), the groups router
(`/api/v1/groups`), the repository classes for users, groups and access grants, and the permission
helpers in `backend/open_webui/utils/access_control/`. The single-tenant model in
`../tools/ground-truth.md` applies: groups organize people for permissions and sharing; they are not
separate organisations.

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is TO BE CONFIRMED.

### 2.1 Pages

| Page | URL | Who can open it | What it shows | Source |
|---|---|---|---|---|
| Admin Panel | `/admin` | Admins | Redirects to `/admin/users`, which redirects to `/admin/users/overview` | `src/routes/(app)/admin/+page.svelte:5-7`; `src/routes/(app)/admin/users/+page.svelte:5-7` |
| Users › Overview | `/admin/users/overview` | Admins | Paginated user table (30 per page), search, **Add User**, per-row Chats, Preview Access, Edit User and Delete User buttons | `src/lib/components/admin/Users.svelte:129-130`; `src/lib/components/admin/Users/UserList.svelte:183-476` |
| Users › Groups | `/admin/users/groups` | Admins | Group list, **New Group**, sort by Members or Name, **Default permissions** entry at the bottom | `src/lib/components/admin/Users.svelte:131-132`; `src/lib/components/admin/Users/Groups.svelte:123-236` |
| One group's editor | `/admin/users/groups?id={group id}` | Admins | Opens that group's Edit User Group dialog on load (the Edit User dialog links here from a user's group chips) | `src/lib/components/admin/Users/Groups/GroupItem.svelte:53-58`; `src/lib/components/admin/Users/UserList/EditUserModal.svelte:123-127` |
| Admin Settings › Authentication | `/admin/settings/authentication` | Admins | **Default User Role** and **Default Group** under **User Access** (detail in `admin-settings-panels.md`) | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-9`; `src/lib/components/admin/Settings/Authentication.svelte:139-170` |
| A user's chat, opened by an admin | `/s/{chat id}` | Admins, when admin chat access is on | The shared-chat viewer, reached from the user's Chats list | `src/lib/components/layout/ChatsModal.svelte:293`; `backend/open_webui/routers/chats.py:1845-1847` |
| Share dialogs | no URL (dialogs inside editors) | Owners and write-holders of an item | Access Control dialog (visibility, access list) | `src/lib/components/workspace/common/AccessControlModal.svelte:30-59` |

The Admin Panel's layout sends any non-admin who opens an `/admin` URL back to `/`
(`src/routes/(app)/admin/+layout.svelte:15-16`); the Users and Groups components repeat that check
(`src/lib/components/admin/Users.svelte:60-63`; `src/lib/components/admin/Users/Groups.svelte:100-104`).
The Users tab labels show counts: **Overview** with the number of accounts and **Groups** with the
number of groups (`src/lib/components/admin/Users.svelte:42-58`, `:98-123`).

### 2.2 Users API (`/api/v1/users`)

"User" in the access column means role `user` or `admin` (`get_verified_user`); "Admin" means role
`admin` (`get_admin_user`). Both refuse other roles with HTTP 401 and the `ACCESS_PROHIBITED` text
(`backend/open_webui/utils/auth.py:567-576`, `:625-631`).

| Method and path | Access | Purpose | Source |
|---|---|---|---|
| `GET /api/v1/users/` | Admin | Paginated list (30 per page) with search, sort and each user's group ids | `backend/open_webui/routers/users.py:79-126` |
| `GET /api/v1/users/all` | Admin | Every user (used by the Admin Settings › Database user export) | `backend/open_webui/routers/users.py:129-134`; `src/lib/components/admin/Settings/Database.svelte:30-51` |
| `GET /api/v1/users/search` | User | Search accounts by name or email fragment, 30 per page (share pickers, mentions) | `backend/open_webui/routers/users.py:137-161` |
| `GET /api/v1/users/groups` | User | The caller's own groups | `backend/open_webui/routers/users.py:169-171` |
| `GET /api/v1/users/permissions` | User | The caller's effective permissions | `backend/open_webui/routers/users.py:179-187` |
| `GET` and `POST /api/v1/users/default/permissions` | Admin | Read or replace the stored default permissions (`user.permissions`) | `backend/open_webui/routers/users.py:411-435` |
| `GET /api/v1/users/default/permissions/defaults` | Admin | The code and environment defaults (`DEFAULT_USER_PERMISSIONS`) used by **Reset to Defaults** | `backend/open_webui/routers/users.py:438-449` |
| `GET /api/v1/users/user/settings`, `POST .../user/settings/update` | User | The caller's own settings (permission filtering described in section 7.5) | `backend/open_webui/routers/users.py:457-562` |
| `GET /api/v1/users/user/status`, `POST .../user/status/update` | User, when `users.enable_status` is on | The caller's status emoji and message | `backend/open_webui/routers/users.py:570-614` |
| `GET` and `POST /api/v1/users/user/info...`, `.../user/variables...` | User | The caller's free-form info and chat variables | `backend/open_webui/routers/users.py:622-698` |
| `GET /api/v1/users/usage` | User | The caller's usage statistics (Settings › Usage) | `backend/open_webui/routers/users.py:706-777` |
| `GET /api/v1/users/{user_id}` | Admin | One user with group names and active flag | `backend/open_webui/routers/users.py:794-811` |
| `GET /api/v1/users/{user_id}/info` | User | Another user's name, email, role, bio, status, group names and active flag | `backend/open_webui/routers/users.py:814-832` |
| `GET /api/v1/users/{user_id}/oauth/sessions` | Admin | A user's stored SSO sessions (no caller in the interface) | `backend/open_webui/routers/users.py:835-846` |
| `GET /api/v1/users/{user_id}/profile/image` | User | A user's avatar (default image when none is usable) | `backend/open_webui/routers/users.py:854-893` |
| `GET /api/v1/users/{user_id}/active` | User | Whether a user is active now | `backend/open_webui/routers/users.py:901-907` |
| `POST /api/v1/users/{user_id}/update` | Admin | Change role, name, email, profile image or password | `backend/open_webui/routers/users.py:915-1034` |
| `DELETE /api/v1/users/{user_id}` | Admin | Delete a user | `backend/open_webui/routers/users.py:1042-1084` |
| `GET /api/v1/users/{user_id}/groups` | Admin | A user's groups (Edit User dialog) | `backend/open_webui/routers/users.py:1092-1096` |
| `GET /api/v1/users/{user_id}/preview` | Admin | Which models, knowledge bases and tools the user can read | `backend/open_webui/routers/users.py:1104-1174` |

### 2.3 Groups API (`/api/v1/groups`)

| Method and path | Access | Purpose | Source |
|---|---|---|---|
| `GET /api/v1/groups/` | User | Admins get every group; others get the groups they belong to, or, with `share=true`, the groups they are allowed to share to | `backend/open_webui/routers/groups.py:36-52` |
| `POST /api/v1/groups/create` | Admin | Create a group | `backend/open_webui/routers/groups.py:60-93` |
| `GET /api/v1/groups/id/{id}` | Admin | One group with member count | `backend/open_webui/routers/groups.py:101-113` |
| `GET /api/v1/groups/id/{id}/info` | User | Name, description, creator id and member count (used to label groups in share lists) | `backend/open_webui/routers/groups.py:116-128` |
| `GET /api/v1/groups/id/{id}/export` | Admin | The group plus member ids (no caller in the interface) | `backend/open_webui/routers/groups.py:141-154` |
| `POST /api/v1/groups/id/{id}/users` | Admin | The group's members (no caller in the interface) | `backend/open_webui/routers/groups.py:162-172` |
| `POST /api/v1/groups/id/{id}/update` | Admin | Save name, description, share setting and permissions | `backend/open_webui/routers/groups.py:180-214` |
| `POST /api/v1/groups/id/{id}/users/add` | Admin | Add members (unknown user ids are dropped first) | `backend/open_webui/routers/groups.py:222-259` |
| `POST /api/v1/groups/id/{id}/users/remove` | Admin | Remove members | `backend/open_webui/routers/groups.py:262-296` |
| `DELETE /api/v1/groups/id/{id}/delete` | Admin | Delete a group | `backend/open_webui/routers/groups.py:304-330` |
| `GET /api/v1/groups/id/{id}/preview` | Admin | Which models, knowledge bases and tools the group's members can read through grants, plus the group's permissions | `backend/open_webui/routers/groups.py:338-402` |

### 2.4 Related Endpoints Outside These Routers

| Method and path | Access | Purpose | Source |
|---|---|---|---|
| `POST /api/v1/auths/add` | Admin | Create an account (Add User form and CSV import) | `backend/open_webui/routers/auths.py:1101-1165` |
| `GET /api/v1/chats/list/user/{user_id}` | Admin, only when `ENABLE_ADMIN_CHAT_ACCESS` is on | A user's chat list (Chats button) | `backend/open_webui/routers/chats.py:736-749` |
| `GET /api/usage` | User; admins only when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off | Active-user count and models in use (user menu) | `backend/open_webui/main.py:2620-2637` |

## 3. Roles and Permissions

### 3.1 The Three Roles

Roles are plain strings on the `user` row (`backend/open_webui/models/users.py:151`). The interface
offers exactly three (`src/lib/components/admin/Users/UserList/EditUserModal.svelte:147-149`;
`src/lib/components/admin/Users/UserList/AddUserModal.svelte:204-206`).

| Role | Can sign in | Can use the application | Admin Panel | How the code treats it |
|---|---|---|---|---|
| `admin` | Yes | Yes, without permission checks | Yes | Passes `get_admin_user` and `get_verified_user`; each permission check is skipped for admins at the place it is made (for example `backend/open_webui/routers/models.py:292-295`; `src/lib/components/layout/Sidebar.svelte:164-172`) |
| `user` | Yes | Yes, limited by effective permissions (section 3.5) and by sharing | No | Passes `get_verified_user`; refused by `get_admin_user` (`backend/open_webui/utils/auth.py:567-576`, `:625-631`) |
| `pending` | Yes | No. The app stops loading data and shows the "Account Activation Pending" screen | No | Refused by both checks with HTTP 401 and the `ACCESS_PROHIBITED` text (`backend/open_webui/utils/auth.py:570-575`); `src/routes/(app)/+layout.svelte:217-219`, `:445-446` |

New accounts get the role in the `ui.default_user_role` setting (code default `pending`), except
that the very first account becomes `admin` (`../tools/ground-truth.md`, Accounts and Access;
`backend/open_webui/routers/auths.py:868-879`). The admin **Add User** form and CSV import set the
role explicitly (section 5.5, 5.6).

The role is re-read from the database on every authenticated request
(`backend/open_webui/utils/auth.py:455`), so changing someone to `pending` blocks their next request
even if they are already signed in. A role change also disconnects that user's live socket
connections so that cached role data is refreshed (`backend/open_webui/events.py:1089-1100`;
`backend/open_webui/socket/main.py:388-404`).

### 3.2 What Admins Can Do That Users Cannot

- Open the Admin Panel and call every admin endpoint (section 2).
- Skip every feature permission: the interface checks `role === 'admin'` before the permission
  (for example `src/lib/components/chat/Navbar.svelte:246`), and the server checks `role != 'admin'`
  before calling `has_permission` (for example `backend/open_webui/routers/users.py:493-547`).
- Share to any group whatever its share setting; non-admins only see groups they may share to
  (`backend/open_webui/routers/groups.py:44-48`).
- Always see the **Public** and **Open** visibility options in share dialogs (for example
  `src/lib/components/chat/ShareChatModal.svelte:163-164`), and keep public grants that a non-admin
  would lose on save (`backend/open_webui/utils/access_control/__init__.py:253-254`).
- With `BYPASS_ADMIN_ACCESS_CONTROL` on (the default), see and manage every workspace item and every
  admin-configured tool or terminal server regardless of sharing (section 3.7).
- With `ENABLE_ADMIN_CHAT_ACCESS` on (the default), list and open any user's chats (section 3.7).
- See base models that have no registered model record; non-admins do not see them, and a chat
  sent to one is refused (`backend/open_webui/utils/models.py:571-574`, `:483-491`;
  `backend/open_webui/utils/access_control/__init__.py:410-413`). With `BYPASS_ADMIN_ACCESS_CONTROL`
  off, admins still see these models but the chat check refuses them too (section 3.7).
  *Precision (2026-10-08):* that holds only while no Model Defaults metadata
  (`models.default_metadata`) is stored; once it is, record-less base models receive default
  metadata, enter the access check, and disappear from the list of admins without the bypass
  (`backend/open_webui/utils/models.py:341-347`, `:533-536`, `:563-574`; see
  `workspace-models-and-model-access.md` section 5.17).

### 3.3 Primary Admin Rules

The **primary admin** is the account with the earliest `created_at`
(`backend/open_webui/models/users.py:715-720`). The code protects it as follows:

1. Only the primary admin can edit the primary admin. Another admin who saves the Edit User dialog
   for it gets HTTP 403 `The requested action has been restricted as a security measure.`
   (`backend/open_webui/routers/users.py:923-933`).
2. The primary admin cannot change their own role away from `admin` (same message,
   `backend/open_webui/routers/users.py:935-940`). The interface already disables the role menu when
   an admin edits their own account (`src/lib/components/admin/Users/UserList/EditUserModal.svelte:140-145`).
3. Nobody can delete the primary admin (HTTP 403, same message,
   `backend/open_webui/routers/users.py:1046-1053`).
4. No admin can delete their own account (HTTP 403, same message,
   `backend/open_webui/routers/users.py:1063`, `:1080-1084`).
5. The Users table shows no Delete button on any `admin` row
   (`src/lib/components/admin/Users/UserList.svelte:448-461`). To remove another (non-primary)
   admin, an admin first changes that person's role to `user` or `pending`, then deletes.
6. If the primary-admin lookup itself fails, the save or delete stops with HTTP 500
   `Could not verify primary admin status.` and a server log line
   (`backend/open_webui/routers/users.py:942-949`, `:1054-1061`).

When "show admin details" is on and no admin email is configured, the primary admin's name and
email are what pending users see on their waiting screen (`backend/open_webui/routers/auths.py:1171-1196`;
detail in `authentication-and-sign-in.md`).

### 3.4 Who Can Do What in This Area

| Action | `admin` | `user` | `pending` |
|---|---|---|---|
| Open Admin Panel › Users and Groups | Yes | No | No |
| Change roles, edit or delete other users, add users, import users | Yes (primary-admin limits in 3.3) | No | No |
| Create, edit and delete groups; change group members and permissions | Yes | No | No |
| Edit Default permissions | Yes | No | No |
| View another user's chats | Yes, when `ENABLE_ADMIN_CHAT_ACCESS` is on | No | No |
| Preview a user's or group's access | Yes | No | No |
| Search other users by name or email; see their name, email, role and bio | Yes | Yes | No |
| See their own groups and effective permissions | Yes | Yes | No |
| Share own items with users and groups | Yes | Yes, if `access_grants.allow_users` / `allow_groups` and the item's sharing permission allow it | No |
| Make an item public (all users) | Yes | Only with the item's public-sharing permission | No |

Sources: section 2 access columns; `backend/open_webui/utils/access_control/__init__.py:223-301`.

### 3.5 How Effective Permissions Are Worked Out

Two functions decide what a non-admin may do
(`backend/open_webui/utils/access_control/__init__.py:35-108`):

- **`has_permission`** (used by server checks) looks at each of the user's groups first. If **any**
  group has the key set to true, the answer is yes. Otherwise it falls back to the stored default
  permissions, filling any key missing from the stored defaults with the code default
  (`backend/open_webui/utils/access_control/__init__.py:97-108`).
- **`get_permissions`** (used to build the permission object the interface receives at sign-in and
  session load) starts from a copy of the stored defaults and merges every group on top with "true
  wins" (`backend/open_webui/utils/access_control/__init__.py:46-72`;
  `backend/open_webui/routers/auths.py:209`, `:291`).

Consequences, all from that logic:

- **Permissions only add.** A group switch set to off does nothing if the defaults or another group
  turn the same key on. The group editor says so under any switch that the defaults keep on:
  `This is a default user permission and will remain enabled.`
  (`src/lib/components/admin/Users/Groups/Permissions.svelte:75-81` and the same notice under each
  switch).
- **To restrict a feature for some people**, turn it off in Default permissions and turn it on in a
  group that contains everyone who should keep it.
- **A group holds its own full set of values.** The **New Group** dialog starts from the current
  default permissions (`src/lib/components/admin/Users/Groups.svelte:113-121`), and **Reset to
  Defaults** on a group copies the current defaults into it
  (`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:63-84`). If an admin later turns a
  default off, every group that still holds `true` for it keeps granting it to its members.
- A group whose stored permissions are empty is listed as **Uses defaults**; any stored value makes
  it **Custom permissions** (`src/lib/components/admin/Users/Groups/GroupItem.svelte:27`,
  `:107-111`). Opening such a group shows the interface's built-in values for unset keys, many of them
  on, and saving stores them (`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:86-99`;
  `src/lib/constants/permissions.ts:1-79`).
- **When changes show.** Server checks read groups and settings on each request. The interface uses
  the permission object loaded when the app starts (`src/routes/+layout.svelte:1279-1287`), so a
  person sees a changed permission reflected in menus and buttons after reloading the page.

### 3.6 Worked Example (Fictional Groups)

Assume Default permissions have **Web Search** on, **Knowledge Access** off and **Allow File
Upload** on. Two fictional groups exist:

| Group | Web Search | Knowledge Access | Allow File Upload |
|---|---|---|---|
| Demo Research Leads | on | on | on |
| Demo Trainees | off | off | off |

| Person (fictional) | Groups | Web Search | Knowledge Access | Allow File Upload | Why |
|---|---|---|---|---|---|
| jane.doe@example.com | Demo Research Leads, Demo Trainees | Yes | Yes | Yes | Any group granting a key is enough |
| john.roe@example.com | Demo Trainees | **Yes** | No | **Yes** | The group's "off" cannot remove what the defaults grant |
| sam.poe@example.com | none | Yes | No | Yes | Defaults only |

To stop Demo Trainees uploading files, the admin turns **Allow File Upload** off in Default
permissions and makes sure every group whose members should keep uploading (here Demo Research
Leads) has it on. Any other group created earlier from the defaults also still holds **on** and must
be checked, because each group carries its own copy.

### 3.7 Admin Visibility Defaults

All three switches are environment variables, read once at start-up and not stored in the `config`
table; the live values are TO BE CONFIRMED.

| Switch | Code default | Effect | Source |
|---|---|---|---|
| `ENABLE_ADMIN_CHAT_ACCESS` | on | Admins get a **Chats** button on each non-admin row of the Users table and can open those chats in the shared-chat viewer; when off, listing another user's chats is refused with `ACCESS_PROHIBITED` | `backend/open_webui/env.py:371`; `backend/open_webui/main.py:2374`; `src/lib/components/admin/Users/UserList.svelte:405-418`; `backend/open_webui/routers/chats.py:748-749`, `:1845-1847` |
| `BYPASS_ADMIN_ACCESS_CONTROL` (falls back to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) | on | Admins see every model, knowledge base, prompt, tool, skill and file regardless of grants, and every admin-configured tool or terminal server; when off, admins see what they own or what is shared with them, like users, but keep access to connections that have no grants. For models, admins with it off still see base models that have no model record, and their chats go through the model check like a user's (see below) | `backend/open_webui/config.py:2084-2092`; `backend/open_webui/routers/knowledge.py:186`; `backend/open_webui/routers/prompts.py:56`; `backend/open_webui/routers/tools.py:75`; `backend/open_webui/routers/files.py:497`; `backend/open_webui/utils/access_control/__init__.py:166-174`; models: `backend/open_webui/utils/models.py:526-528`, `:565-574`; `backend/open_webui/main.py:1150` |
| `BYPASS_MODEL_ACCESS_CONTROL` | off | When on, every signed-in user sees and may use every model without model access checks: the model list, the chat path, custom pipe models and the provider routers skip them. Two places check whatever this says: message action buttons for non-admins, and the Ollama router's OpenAI-compatible `/ollama/v1/...` endpoints | `backend/open_webui/env.py:832`; `backend/open_webui/utils/models.py:524-528`; `backend/open_webui/main.py:1150`; `backend/open_webui/utils/chat.py:156-157`; `backend/open_webui/functions.py:288-290`; `backend/open_webui/routers/openai.py:463`, `:938`, `:1504-1506`, `:1900`; `backend/open_webui/routers/ollama.py:502`, `:855`, `:1119-1121`, `:1511`; still checked: `backend/open_webui/utils/actions.py:58-59`; `backend/open_webui/routers/ollama.py:1246`, `:1298`, `:1354`, `:1406`, `:1464` |

**Model access control in brief** (full detail in `workspace-models-and-model-access.md`): a non-admin
sees a model when they own its model record or a read grant reaches them (public, direct or through
a group) (`backend/open_webui/utils/models.py:540-570`). Arena models are matched instead against
the access list stored with each arena in the `evaluation.arena.models` setting; when arenas are on
(`evaluation.arena.enable`, on in code) and none are configured, the built-in **Arena Model** is
offered, and with no access list it is not offered to non-admins
(`backend/open_webui/utils/models.py:115-149`, `:551-561`, `:466-480`;
`backend/open_webui/config.py:2054`, `:2067-2078`). Base models that have no model record are
admin-only (`backend/open_webui/utils/models.py:571-574`). A custom model built on another model is
refused with `Model not found` when the person cannot read every model in the chain
(`backend/open_webui/utils/access_control/__init__.py:304-358`). The chat path runs this check in
`backend/open_webui/utils/models.py:465-521` (refusals reach the chat as HTTP 400 with that text,
`backend/open_webui/main.py:1157-1161`, `:1640-1645`); the provider routers use the version in
`backend/open_webui/utils/access_control/__init__.py:304-413`, which skips admins (for example
`backend/open_webui/routers/openai.py:1535-1537`; `backend/open_webui/routers/ollama.py:1151-1153`).

What a chat message to one of the site's models meets, in order (`chat_completion`,
`backend/open_webui/main.py:1110-1185`):

| Step | Check | Applies to | Refusal shown | Source |
|---|---|---|---|---|
| 1 | The model is in the server's current model list | Everyone | `Model not found` (HTTP 400) | `backend/open_webui/main.py:1128-1129` |
| 2 | Model access: ownership or a read grant, then every model in the base-model chain; for an arena, its own access list; a model with no model record is refused | Non-admins, and admins while `BYPASS_ADMIN_ACCESS_CONTROL` is off; nobody while `BYPASS_MODEL_ACCESS_CONTROL` is on | `Model not found` (HTTP 400) | `backend/open_webui/main.py:1149-1161`; `backend/open_webui/utils/models.py:465-521` |
| 3 | A custom model's base model is in the current model list. If it is not and `ENABLE_CUSTOM_MODEL_FALLBACK` is on (off in code), the first model in `ui.default_models` is used instead when available, and step 2 checks that model rather than the missing one | Everyone | `Model not found` (HTTP 400) | `backend/open_webui/main.py:1133-1147`, `:1152-1159`, `:1180-1185`; `backend/open_webui/env.py:1033` |
| 4 | Step 2 again on the model actually sent; for an arena, the model it picked at random | `user` role, unless `BYPASS_MODEL_ACCESS_CONTROL` is on | `Model not found` as the response's error | `backend/open_webui/utils/middleware.py:2403-2427`; `backend/open_webui/utils/chat.py:156-157`, `:198-203`; `backend/open_webui/main.py:1686-1710` |

Steps 1 and 3 concern availability, not access: they refuse admins and owners too and write no
`Model access denied` log line (section 10.1). The chat screen shows an HTTP refusal as a pop-up and
as the response's error (`src/lib/components/chat/Chat.svelte:3643-3660`). Because step 2 applies to
admins while `BYPASS_ADMIN_ACCESS_CONTROL` is off, a base model with no model record, which those
admins still see in their list (`backend/open_webui/utils/models.py:571-574`), is refused when they
chat with it (`backend/open_webui/utils/models.py:483-491`). (While Model Defaults metadata is
stored, those admins no longer see such models at all; see the precision note in section 3.2.)

## 4. Key Concepts and Terminology

| Term | Meaning in this code | Source |
|---|---|---|
| Role | `admin`, `user` or `pending`, stored on the `user` row; decides access to admin pages and whether the app works at all | `backend/open_webui/models/users.py:151`; section 3.1 |
| Pending user | An account whose role is `pending` (or any value other than `user` or `admin`): it can sign in but sees only the waiting screen. "Approving" or "activating" means changing the role to `user`. "Suspending" someone means setting the role back to `pending` | `src/routes/(app)/+layout.svelte:445-446`; `../tools/ground-truth.md` |
| Primary admin | The earliest-created account; protected from edits by others, demotion and deletion | `backend/open_webui/models/users.py:715-720`; section 3.3 |
| Group | A named set of users with its own permission values and share setting. Not a tenant | `backend/open_webui/models/groups.py:37-52` |
| Group member | One `group_member` row linking a user to a group | `backend/open_webui/models/groups.py:73-86` |
| Default User Role | Setting `ui.default_user_role`: the role given to accounts created by sign-up, LDAP or trusted headers, and by SSO unless SSO role mapping is on (see `sso-oauth-oidc-and-scim.md`) | `backend/open_webui/config.py:1720`, `:3096`; `backend/open_webui/routers/auths.py:868`; `backend/open_webui/utils/oauth.py:1531-1546` |
| Default Group | Setting `ui.default_group_id`: a group new accounts are added to when they are created through sign-up, the Add User form or CSV, LDAP, SSO or trusted headers | `backend/open_webui/config.py:1722`, `:3097`; `backend/open_webui/utils/groups.py:8-24`; `backend/open_webui/routers/auths.py:669-673`, `:881-885`, `:1132-1136`; `backend/open_webui/utils/oauth.py:2137-2138` |
| Default permissions | Setting `user.permissions`: the permission values every `user` starts with. Edited from the Groups tab ("applies to all users with the "user" role") | `backend/open_webui/config.py:1940-2022`, `:3101`; `src/lib/components/admin/Users/Groups.svelte:209-235` |
| Permission key | A dotted name such as `chat.file_upload`, in one of six sections: `workspace`, `sharing`, `access_grants`, `chat`, `features`, `settings` | `backend/open_webui/routers/users.py:193-285` |
| Effective permissions | What a user can actually do: defaults plus every group, where any "on" wins | `backend/open_webui/utils/access_control/__init__.py:35-108` |
| Uses defaults / Custom permissions | Group list labels: a group with no stored permission values shows **Uses defaults**; any stored value shows **Custom permissions** | `src/lib/components/admin/Users/Groups/GroupItem.svelte:27`, `:106-112` |
| Who can share to this group | A group's share setting: **No one** (`false`), **Members** (`"members"`, the default for new groups) or **Anyone** (`true`). It decides which non-admins see the group in share pickers | `src/lib/components/admin/Users/Groups/General.svelte:69-102`; `backend/open_webui/env.py:1023-1027`; `backend/open_webui/models/groups.py:203-228` |
| Access grant | One row saying a principal may `read` or `write` one resource | `backend/open_webui/models/access_grants.py:25-45` |
| Principal | Who a grant is for: `user` (one person, or `*` meaning every signed-in user), `group`, or `anyone` (`*` only, read only: no sign-in needed) | `backend/open_webui/models/access_grants.py:14-17`, `:171-178` |
| Resource types | The kinds of item that take grants in this version: `model`, `knowledge`, `prompt`, `tool`, `skill`, `note`, `folder`, `channel`, `calendar`, `shared_chat` | calls to `set_access_grants` and `has_access` across `backend/open_webui/routers/` |
| Read / Write | Read lets the principal see and use the item; write also lets them change it. Choosing **Write** in a share dialog adds both a read and a write grant; switching back to **Read** removes only the write grant | `src/lib/components/workspace/common/AccessControl.svelte:312-325` |
| Visibility | The share dialog's first menu: **Private** ("Only select users and groups with permission can access"), **Public** ("Accessible to all users", a `user:*` read grant) or **Open** ("Anyone with the link can view", an `anyone:*` read grant) | `src/lib/components/workspace/common/AccessControl.svelte:217-245`, `:523-549` |
| Owner | The user whose id is on the item. Owners always have access to their own items without a grant | `backend/open_webui/models/access_grants.py:759-761`, `:824-829` |
| Admin bypass | `BYPASS_ADMIN_ACCESS_CONTROL`: admins see every workspace item regardless of grants | section 3.7 |
| Admin chat access | `ENABLE_ADMIN_CHAT_ACCESS`: admins can list and open other users' chats | section 3.7 |
| Model access control | The rule that non-admins only see models they own or that are shared with them | section 3.7 |
| Active | A user whose `last_active_at` is within the last 180 seconds (3 minutes) | `backend/open_webui/models/users.py:910-925`; `src/lib/components/admin/Users/UserList.svelte:369` |
| Preview Access / Preview | Admin read-outs of which models, knowledge bases and tools a user (Users table eye icon) or a group (group editor **Preview** tab) can read | `backend/open_webui/routers/users.py:1104-1174`; `backend/open_webui/routers/groups.py:338-402` |
| Group sync | When SSO, LDAP or trusted-header group management is on, sign-in replaces a user's memberships with the groups named by the identity provider (detail in `sso-oauth-oidc-and-scim.md`) | `backend/open_webui/models/groups.py:516-572`; `backend/open_webui/utils/oauth.py:1729-1800` |

## 5. Workflows (Step by Step)

All workflows in this section are admin tasks unless marked otherwise. Tier 1 reads these to explain
them; it does not perform them.

### 5.1 Approve a Pending User

1. Open Admin Panel › Users › **Overview** (`/admin/users/overview`). Pending accounts show
   **pending** in the Role column (grey text). Sort by **Role** or search by name or email
   (`src/lib/components/admin/Users/UserList.svelte:189-195`, `:251-273`, `:381-392`).
2. Click the role text (its accessible name is "Change User Role") or the pencil icon (**Edit
   User**). Both open the **Edit User** dialog (`src/lib/components/admin/Users/UserList.svelte:382-391`,
   `:435-446`). The page also says `ⓘ Click on the user role button to change a user's role.`
   (`src/lib/components/admin/Users/UserList.svelte:470-472`).
3. In **Role**, choose **User** (or **Admin**) and press **Save**
   (`src/lib/components/admin/Users/UserList/EditUserModal.svelte:136-151`, `:220-227`).
4. The dialog posts role, name, email and profile image to
   `POST /api/v1/users/{user_id}/update`; a blank **New Password** is left out
   (`src/lib/apis/users/index.ts:579-611`). The server saves the role, publishes `user.role_updated`
   and disconnects the person's live socket connections (`backend/open_webui/routers/users.py:972-1013`;
   `backend/open_webui/events.py:1089-1100`).
5. The person is not told. Their waiting screen stays until they press **Check Again**, which
   reloads the app at `/`, or reload the page themselves
   (`src/lib/components/layout/Overlay/AccountPending.svelte:59-67`). The application sends no email
   (`../tools/ground-truth.md`, Contacts).

The dialog closes and the table refreshes on success; no success message is shown
(`src/lib/components/admin/Users/UserList/EditUserModal.svelte:46-55`).

### 5.2 Change a Role: Promote, Demote or Suspend

The same Edit User dialog changes any role, within the primary-admin rules in section 3.3.

- **Promote to Admin.** Takes effect on the person's next request: admin pages, admin endpoints and
  the admin bypasses in section 3.7.
- **Demote an admin to User.** Allowed for any admin except the primary admin. The role menu is
  disabled when you edit your own account, so an admin cannot demote themselves here
  (`src/lib/components/admin/Users/UserList/EditUserModal.svelte:140-145`).
- **Suspend (set to Pending).** The person's next request is refused with HTTP 401 and the
  `ACCESS_PROHIBITED` text; after a reload they see the waiting screen. Their chats and other
  content are untouched (`backend/open_webui/utils/auth.py:567-576`).
- With SSO role management on, a role set here can be replaced by the identity provider's mapping at
  the person's next SSO sign-in (detail in `sso-oauth-oidc-and-scim.md`;
  `backend/open_webui/utils/oauth.py:1531-1546`).

### 5.3 Edit a User's Name, Email, Profile Image or Password

The Edit User dialog shows the name, the account's creation date, the person's groups as links to
each group's editor, **Role**, **Name**, **Email**, the SSO identifiers under **OAuth ID** when the
account is linked to a provider, and **New Password**
(`src/lib/components/admin/Users/UserList/EditUserModal.svelte:91-216`). The OAuth ID values are
personal identifiers; handle screenshots of this dialog with care.

On **Save** the server (`backend/open_webui/routers/users.py:951-1034`):

1. Rejects a new email that another account already uses with `Uh-oh! This email is already
   registered. Sign in with your existing account or choose another email to start anew.`; otherwise
   stores it in lower case on both the `user` and `auth` rows (`:954-960`, `:978-980`).
2. When **New Password** is filled, checks the password rules (the messages are catalogued in
   `authentication-and-sign-in.md`), stores the new hash, and asks for the person's existing sign-ins
   to be ended (`:962-970`). Ending existing sign-ins needs Redis; without it the server logs
   `Cannot revoke tokens for user {user_id}: Redis is not configured, existing sessions stay valid until expiry.`
   and those sessions keep working until they expire (`backend/open_webui/utils/auth.py:349-371`;
   `../tools/ground-truth.md`, Accounts and Access).
3. Publishes `user.updated` (with the list of changed fields), `user.role_updated` when the role
   changed, and `auth.password_changed` when a password was set (`:993-1023`).

### 5.4 Delete a User

1. In the Users table, click the trash icon (**Delete User**). It appears only on rows whose role is
   not `admin` (`src/lib/components/admin/Users/UserList.svelte:448-461`).
2. Confirm the dialog, which shows the default heading `Confirm your action` and text
   `This action cannot be undone. Do you wish to continue?`
   (`src/lib/components/admin/Users/UserList.svelte:136-141`;
   `src/lib/components/common/ConfirmDialog.svelte:139-154`).
3. The page calls `DELETE /api/v1/users/{user_id}`; on success the table refreshes without a
   message, and on failure the server's text appears in a pop-up
   (`src/lib/components/admin/Users/UserList.svelte:59-73`).

What the server does, in order (`backend/open_webui/routers/users.py:1046-1084`;
`backend/open_webui/models/auths.py:228-239`; `backend/open_webui/models/users.py:849-863`;
`backend/open_webui/models/chats.py:2500-2519`):

1. Refuses the primary admin and the admin's own account (section 3.3).
2. Removes the person from every group.
3. Deletes the shared-chat snapshots the person created, unlinks automation runs from the person's
   chats, deletes the chat messages and then the chats.
4. Deletes the `user` row, then the `auth` row (sign-in credentials).
5. Publishes `user.deleted` and disconnects the person's live socket connections
   (`backend/open_webui/events.py:1089-1100`).

Each repository step opens its own database session unless `DATABASE_ENABLE_SESSION_SHARING` is on
(code default off), so a failure part-way leaves the earlier steps done
(`backend/open_webui/internal/db.py:529-535`; `backend/open_webui/env.py:366`). If chat deletion
fails, the server answers HTTP 500 `Oops! Something went wrong. We encountered an issue while trying
to delete the user. Please give it another shot.`, and the person may already have been removed from
their groups.

What is **left behind** (no code path in this area removes it; `../tools/ground-truth.md` lists the
same):

| Left behind | Effect |
|---|---|
| Files, knowledge bases, custom models, prompts, tools, skills, notes, memories, folders, feedback, channel messages, automations and calendar data owned by the person | They keep the deleted person's id as owner. No ownership-transfer feature exists in the backend (a search for one found none). Items the person shared stay usable by whoever they were shared with; admins with admin bypass on still see them |
| Access grants that name the person | They stay in `access_grant` but no longer match anyone |
| Rows that rely on a database cascade, for example chat-to-file links | Removed by PostgreSQL; on SQLite the code does not switch on foreign-key enforcement, so they can remain (`backend/open_webui/models/chats.py:223`; `backend/open_webui/internal/db.py:335-395`). Detail in `database-schema-identity-chats-and-config.md` |

Other account-related records outside the chat and group tables are also not removed by this path;
the full list belongs to `database-schema-identity-chats-and-config.md`. Whether any
credential-related records remain is security-sensitive: refer to the platform maintainer and U of T
Information Security (security.utoronto.ca).

A deleted person who still has the app open gets `Your session has expired or the token is invalid.
Please sign in again.` on their next request, because their account no longer exists
(`backend/open_webui/utils/auth.py:455-460`). There is no undo in the code; recovery would depend
on database backups, which are TO BE CONFIRMED.

### 5.5 Add a Single User

1. Users › Overview › **Add User** (`src/lib/components/admin/Users/UserList.svelte:213-220`).
2. On the **Form** tab, choose **Role** (the form starts at `user`), and enter **Name**, **Email**
   and **Password** (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:24-38`,
   `:192-258`).
3. Press **Save**. The page calls `POST /api/v1/auths/add` with a generated initials avatar
   (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:46-63`).
4. The server checks the email format, refuses an email already in use, checks the password rules,
   creates the `auth` and `user` rows with the chosen role, adds the account to the Default Group (if
   one is set) and publishes `user.created` with source `admin`
   (`backend/open_webui/routers/auths.py:1101-1165`).
5. The dialog closes and the list refreshes; failures appear as a pop-up with the server's text.

The new person is not notified by the system. How the admin passes on the address and initial
password is an organisational process, TO BE CONFIRMED.

### 5.6 Import Users from a CSV File

1. Users › Overview › **Add User** › **CSV Import**
   (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:180-188`).
2. Optionally download the template (**Click here to download user import template file.**), which
   is `/static/user-import.csv` and contains only the header line `Name,Email,Password,Role`
   (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:285-295`;
   `static/static/user-import.csv`; `backend/open_webui/static/user-import.csv`).
3. Choose the file and press **Save**.

File format, as the parser reads it (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:65-134`):

- The **first line is a header and is skipped**, whatever it says.
- Every later line is one account: `Name,Email,Password,Role`, in that order. Role must be `admin`,
  `user` or `pending` in any letter case. Example with fictional people and placeholder passwords:

  ```
  Name,Email,Password,Role
  Jane Doe,jane.doe@example.com,<initial password>,user
  John Roe,john.roe@example.com,<initial password>,pending
  ```

- Lines are split on every comma with no support for quotes, so a name or password that contains a
  comma breaks its line. Spaces around each value are trimmed, which also removes Windows line
  endings.
- A line without exactly four values, or with any other role, is skipped with
  `Row {idx + 1}: invalid format.` The number is the line number in the file, counting the header as
  line 1. A blank last line (a file that ends with a line break, as most editors save it) produces
  this message for that empty line; the other lines still import.
- Valid lines are sent ten at a time through the same server path as 5.5 (format check, duplicate
  check, password rules, Default Group, `user.created`). Each failure shows `Row {idx + 1}: {error}`
  with the server's text.
- At the end the page shows `Successfully imported {userCount} users.`, counting only accounts that
  were created (it can read 0).
- Pressing **Save** with no file chosen shows `File not found.`

The CSV contains initial passwords and email addresses; treat it as sensitive and do not attach it
to tickets. The user export on Admin Settings › Database writes `id,name,email,role` columns, which
is not the import format (`src/lib/components/admin/Settings/Database.svelte:30-51`).

### 5.7 View a User's Chats

Available only when `ENABLE_ADMIN_CHAT_ACCESS` is on, and only on rows whose role is not `admin`.

1. Click the speech-bubble icon (**Chats**) on the person's row
   (`src/lib/components/admin/Users/UserList.svelte:405-418`).
2. A list titled `{user}'s Chats` opens (names longer than 32 characters are shortened), with search
   and sorting; an empty list reads `No chats found for this user.`
   (`src/lib/components/admin/Users/UserList/UserChatsModal.svelte:107-124`).
3. Clicking a chat opens it in the shared-chat viewer at `/s/{chat id}`
   (`src/lib/components/layout/ChatsModal.svelte:293`; `backend/open_webui/routers/chats.py:1845-1847`).

Chats can contain personal and health information. When admins may open them is a policy question,
TO BE CONFIRMED; the code only checks the role and the switch.

### 5.8 Preview What a User Can Reach

1. Click the eye icon (**Preview Access**) on a row whose role is not `admin`
   (`src/lib/components/admin/Users/UserList.svelte:420-433`).
2. The **User Preview** dialog lists the person's **Groups**, then **Models**, **Knowledge** and
   **Tools** they can read. Empty sections say `No models accessible`, `No knowledge bases
   accessible` or `No tools accessible`; when only some items are reachable a line reads
   `{count} of {total} accessible` (`src/lib/components/admin/UserPreviewModal.svelte:35-175`).

What it counts (`backend/open_webui/routers/users.py:1104-1174`): active model records, all knowledge
bases and all tools that the person owns or that a read grant reaches (public, direct or through one
of their groups). The totals are all active model records, all knowledge bases and all tools.

What it does **not** reflect: base models from connections that have no model record (admin-only),
arena models (they live in settings, not in model records; section 3.7),
`BYPASS_MODEL_ACCESS_CONTROL`, the base-model chain check that can still refuse a custom model with
`Model not found` (section 3.7), whether a custom model's base model is currently offered by a
connection (section 3.7, step 3), feature permissions, and other item types (prompts, skills, notes,
channels, chats). A model listed in the preview can therefore still fail for the person.

### 5.9 Create a Group

1. Users › **Groups** › **New Group** (`src/lib/components/admin/Users/Groups.svelte:176-183`).
2. The **Add User Group** dialog has two tabs (`src/lib/components/admin/Users/Groups.svelte:113-121`;
   `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:138-148`):
   - **General**: **Name** (required), **Description**, and **Who can share to this group**
     (`src/lib/components/admin/Users/Groups/General.svelte:17-102`).
   - **Permissions**: every switch, pre-set to a copy of the current Default permissions.
3. Press **Save**. The page calls `POST /api/v1/groups/create`; the server fills in the share setting
   from `DEFAULT_GROUP_SHARE_PERMISSION` if none was chosen, stores the group with the admin as
   creator and publishes `group.created`; the page shows `Group created successfully`
   (`src/lib/components/admin/Users/Groups.svelte:71-81`; `backend/open_webui/routers/groups.py:60-93`;
   `backend/open_webui/models/groups.py:137-173`).

Members cannot be added while creating: the **Users** and **Preview** tabs exist only when an
existing group is opened (`src/lib/components/admin/Users/Groups/GroupItem.svelte:61-70`). The code
does not stop two groups having the same name (`backend/open_webui/models/groups.py:37-52`), and SSO
and LDAP group sync match groups by name (`backend/open_webui/models/groups.py:516-526`), so
duplicate names make sync results hard to predict.

### 5.10 Add or Remove Group Members

1. Open the group from the Groups list (click its row) and choose the **Users** tab.
2. The table lists every account with a checkbox in the **MBR** column, members first by default,
   with **Name**, **Role** and **Last Active** (`src/lib/components/admin/Users/Groups/Users.svelte:99-100`,
   `:357-515`; `backend/open_webui/models/users.py:614-631`). Search filters by name or email.
3. Ticking a box adds that person **immediately**; unticking removes them immediately. There is no
   Save step for membership (`src/lib/components/admin/Users/Groups/Users.svelte:142-163`,
   `:470-476`). Each change publishes `group.member_added` or `group.member_removed`
   (`backend/open_webui/routers/groups.py:222-296`).

**Import members from a CSV file** (`src/lib/components/admin/Users/Groups/Users.svelte:65-84`,
`:172-262`, `:309-353`):

- **Import** › **Download CSV Template** saves `group-import.csv` containing `Name,Email`. The menu
  also says `CSV: Name,Email`.
- **Import** › **Import CSV** reads the file: the first line is skipped as a header; blank lines are
  ignored; each line needs exactly two values, and only the second (the email) is used.
- Each email is matched exactly (ignoring letter case) against **existing** accounts; the import does
  not create accounts. Unknown emails show `Row {idx + 1}: User not found.`; badly shaped lines show
  `Row {idx + 1}: Invalid format.`
- When at least one person was added the page shows `Successfully imported {userCount} users.`,
  counting the increase in members.

Membership changes affect server checks on the member's next request and their menus after a
reload. With SSO, LDAP or trusted-header group management on, memberships added by hand can be
removed again at the person's next sign-in (section 4, Group sync).

### 5.11 Edit a Group's Permissions

1. Open the group › **Permissions** tab. The switches and their meaning are listed in section 7.5.
2. A switch that is off in the group but on in Default permissions shows `This is a default user
   permission and will remain enabled.` (this hint appears when editing an existing group, because
   only that dialog receives the defaults: `src/lib/components/admin/Users/Groups/GroupItem.svelte:61-70`).
3. Some switches appear only when their parent is on: import and export under each Access switch;
   each "Public Sharing" switch under its "Sharing" switch; **Chats Public Sharing** and **Chats Open
   Sharing** under **Allow Chat Share**; **Calendars Public Sharing** under **Calendar**; **Allow
   Chat Valves**, **Allow Chat System Prompt** and **Allow Chat Params** under **Allow Chat
   Controls**; **Enforce Temporary Chat** under **Allow Temporary Chat**. **Tools Access** is shown
   only when plugins are enabled (`ENABLE_PLUGINS`)
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:54-81`, `:141-185`, `:253-272`,
   `:478-537`, `:640-691`, `:935-954`; `backend/open_webui/main.py:2353`).
4. Press **Save**; the page shows `Group updated successfully`
   (`src/lib/components/admin/Users/Groups/GroupItem.svelte:29-39`). The whole set of values is
   stored on the group.

**Reset to Defaults** (bottom left of the Permissions tab) asks `Are you sure you want to reset all
permissions to their default values? You will still need to save to apply the changes.`, then copies
the **current** Default permissions into the form and shows `Permissions reset to defaults`. Nothing
is stored until **Save** (`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:63-84`,
`:124-133`, `:293-310`).

### 5.12 Set Who Can Share to a Group

Open the group › **General** › **Setting** › **Who can share to this group**, choose an option and
press **Save** (`src/lib/components/admin/Users/Groups/General.svelte:69-102`).

| Option | Stored value | Which non-admins see the group in share pickers |
|---|---|---|
| **No one** | `false` | Nobody |
| **Members** | `"members"` | Only members of the group |
| **Anyone** | `true` | Every user |

Admins see every group in share pickers whatever this says (`backend/open_webui/routers/groups.py:44-48`;
`backend/open_webui/models/groups.py:203-228`). New groups take the value of
`DEFAULT_GROUP_SHARE_PERMISSION` (code default `members`; `true` means Anyone; any other value means
No one) (`backend/open_webui/env.py:1023-1027`). The setting controls who can share **to** the group;
it does not change what members can see.

### 5.13 Delete a Group

1. Open the group › **General** › **Actions** › **Delete**
   (`src/lib/components/admin/Users/Groups/General.svelte:104-118`).
2. Confirm the dialog (`Confirm your action` / `This action cannot be undone. Do you wish to
   continue?`) (`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:116-122`).
3. The page calls `DELETE /api/v1/groups/id/{id}/delete` and shows `Group deleted successfully`;
   the server publishes `group.deleted` (`src/lib/components/admin/Users/Groups/GroupItem.svelte:41-51`;
   `backend/open_webui/routers/groups.py:304-330`).

Effects:

- Members lose whatever the group granted (permissions and shared items) on their next request.
- Access grants that name the group stay in `access_grant` but match no one.
- Membership rows are removed by the database cascade on PostgreSQL. On SQLite the code does not
  switch on foreign-key enforcement, so they can remain; they have no effect because group look-ups
  join the `group` table (`backend/open_webui/models/groups.py:79-83`, `:305-313`;
  `backend/open_webui/internal/db.py:335-395`).
- If the group was the Default Group, new accounts are silently no longer added to any group: the
  assignment finds no group and returns without an error
  (`backend/open_webui/utils/groups.py:20-24`; `backend/open_webui/models/groups.py:582-585`).

### 5.14 Edit Default Permissions

1. Users › **Groups**, then the **Default permissions** row at the bottom ("applies to all users with
   the "user" role") › **Edit** (`src/lib/components/admin/Users/Groups.svelte:209-235`).
2. The **Edit Default Permissions** dialog has only the Permissions tab
   (`src/lib/components/admin/Users/Groups.svelte:238-246`).
3. Press **Save**. The page calls `POST /api/v1/users/default/permissions`, which stores the whole
   object in the `user.permissions` setting and publishes `user.permissions_updated`; the page shows
   `Default permissions updated successfully` (`src/lib/components/admin/Users/Groups.svelte:84-98`;
   `backend/open_webui/routers/users.py:424-435`).

**Reset to Defaults** here (tooltip `Reset all permissions to their initial configuration values`)
loads the code and environment defaults (`USER_PERMISSIONS_*`) rather than the stored ones
(`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:63-69`, `:294-300`;
`backend/open_webui/routers/users.py:438-449`). Saving Default permissions does not change any group;
groups keep their own copies (section 3.5).

### 5.15 Set the Default User Role and Default Group

Admin Settings › **Authentication** › **User Access** (`/admin/settings/authentication`):

- **Default User Role** ("Role assigned to new users when they create an account.") with `pending`,
  `user` or `admin`; stored as `ui.default_user_role`.
- **Default Group** ("Group assigned to new users by default.") with **None** or any group; stored
  as `ui.default_group_id`.

(`src/lib/components/admin/Settings/Authentication.svelte:139-170`;
`src/lib/i18n/locales/en-US/translation.json:2058-2061`.) Both apply only when an account is
created; changing them does not touch existing accounts. The default group is applied on sign-up,
trusted-header sign-in, Add User and CSV import, LDAP and SSO account creation
(`backend/open_webui/routers/auths.py:669-673`, `:881-885`, `:1132-1136`;
`backend/open_webui/utils/oauth.py:2137-2138`). The SCIM code path does not call it (no other caller
of `apply_default_group_assignment` exists in `backend/open_webui`). With SSO group management on,
the sign-in sync that runs right after account creation can remove the default group again unless
the identity provider's group claim names it (`backend/open_webui/utils/oauth.py:2158-2165`,
`:1730-1763`).

### 5.16 Share an Item (Any Signed-In User)

The same Access Control panel is used for most item types
(`src/lib/components/workspace/common/AccessControl.svelte`):

1. In the item's editor, press **Access** (lock icon; `src/lib/components/common/AccessButton.svelte:15-23`).
   The **Access Control** dialog opens (`src/lib/components/workspace/common/AccessControlModal.svelte:30-59`).
2. Choose the visibility (`src/lib/components/workspace/common/AccessControl.svelte:517-549`):
   **Private** (`Only select users and groups with permission can access`), **Public**
   (`Accessible to all users`) or, where offered, **Open** (`Anyone with the link can view`). If
   you may not make the item public, hovering the menu shows `You do not have permission to make
   this public` and the Public option is absent unless the item is already public.
3. For items that support editing by others, a public item also offers **Allow public write
   access** (`src/lib/components/workspace/common/AccessControl.svelte:553-565`).
4. Under **Access List**, press **Add Access**. The **Add Access** dialog lists the groups you may
   share to and lets you search people by name or email. It shows only the first 30 matches,
   sorted by name, with no further pages, so a person not listed is found by typing more of their
   name or email. Your own account and anyone already on the list are hidden. Tick entries and press
   **Add** (`src/lib/components/workspace/common/AddAccessModal.svelte:19-73`;
   `src/lib/components/workspace/common/MemberSelector.svelte:38-98`, `:114-322`;
   `backend/open_webui/routers/users.py:79`, `:137-161`).
5. Each entry has a **Read** / **Write** menu where the item supports writing, and an **X** to
   remove it. With no entries and Private visibility the panel says `No access grants. Private to you.`
   (`src/lib/components/workspace/common/AccessControl.svelte:568-702`).
6. How the change is saved depends on the item. For an existing prompt, tool, skill, note or
   knowledge base, each change in the panel is saved at once and shows `Saved` (a failure shows the
   server's text) (`src/lib/components/workspace/Prompts/PromptEditor.svelte:303-311`;
   `src/lib/components/workspace/Tools/ToolkitEditor.svelte:215-222`;
   `src/lib/components/workspace/Skills/SkillEditor.svelte:101-108`;
   `src/lib/components/notes/NoteEditor.svelte:1001-1008`;
   `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1229-1236`). A model's access is
   saved with the model (`src/lib/components/workspace/Models/ModelEditor.svelte:600-608`). A
   folder's access is saved at once and the list is refreshed from what the server kept
   (`src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:44-54`). A shared chat's
   access is saved at once with `Access updated` (`src/lib/components/chat/ShareChatModal.svelte:78-85`).
7. On every save the server first removes any entry the person was not allowed to add (section
   5.17), then replaces all of the item's grants with the result
   (`backend/open_webui/utils/access_control/__init__.py:223-301`;
   `backend/open_webui/models/access_grants.py:443-478`). Except for folders, the open panel keeps
   showing what was chosen rather than what was kept, so a removed entry disappears only when the
   dialog is opened again.

Where the panel appears and which permissions shape it:

| Item | Where | Access List shown when | Public option when | Notes | Source |
|---|---|---|---|---|---|
| Model | Workspace › Models editor; Admin Settings › Models for base models | `sharing.models` or admin | `sharing.public_models` or admin | Read and Write for workspace models; Read only when an admin edits a base model's access | `src/lib/components/workspace/Models/ModelEditor.svelte:51`, `:600-608`; `src/lib/components/admin/Settings/Models.svelte:1282-1285` |
| Knowledge base | Knowledge base page and create form | `sharing.knowledge` or admin | `sharing.public_knowledge` or admin | | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1220-1237`; `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:149-154` |
| Prompt | Workspace › Prompts editor | `sharing.prompts` or admin | `sharing.public_prompts` or admin | | `src/lib/components/workspace/Prompts/PromptEditor.svelte:295-302` |
| Tool | Workspace › Tools editor | `sharing.tools` or admin | `sharing.public_tools` or admin | | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:207-214` |
| Skill | Workspace › Skills editor | `sharing.skills` or admin | `sharing.public_skills` or admin | | `src/lib/components/workspace/Skills/SkillEditor.svelte:93-100` |
| Note | Note editor | `sharing.notes` or admin | `sharing.public_notes` or admin | | `src/lib/components/notes/NoteEditor.svelte:992-999` |
| Folder | Sidebar folder › share | `sharing.folders` or admin | Never (no public option) | New entries default to Write | `src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:74-84` |
| Shared chat | Share dialog, after a link exists | Always | `sharing.public_chats` or admin | **Open** offered with `sharing.open_chats` or admin; each change saves at once and shows `Access updated` | `src/lib/components/chat/ShareChatModal.svelte:78-85`, `:158-170` |
| Standard channel | Channel dialog | Always | Always offered in the panel | Group channels use a simpler **Visibility** menu (`Visible to all users` / `Only invited users can access`) | `src/lib/components/layout/Sidebar/ChannelModal.svelte:236-245`; `src/lib/components/workspace/common/Visibility.svelte:12-55` |
| Tool servers, terminal servers, external knowledge | Admin settings dialogs | Always | Always | Admin-only screens; grants stored in settings, and no grants means admin-only | `src/lib/components/AddToolServerModal.svelte:1092`; `src/lib/components/AddTerminalServerModal.svelte:1039`; `src/lib/components/admin/Settings/ExternalKnowledge.svelte:772-775`; `backend/open_webui/utils/access_control/__init__.py:151-179` |

In every row, people and groups can be added only when `access_grants.allow_users` and
`access_grants.allow_groups` allow it (or the sharer is an admin), using the values the interface
loaded at sign-in.

### 5.17 Why a Share Can Silently Not Take Effect

The save succeeds and no error appears in each of these cases:

1. **Public without permission.** A non-admin without the item's public-sharing permission who
   saves a Public (or public-write) setting has those grants removed on save
   (`backend/open_webui/utils/access_control/__init__.py:256-274`). The dialog normally hides the
   option, but an item that was already public still shows it.
2. **People or groups without permission.** Without `access_grants.allow_users` the named people are
   removed on save; without `access_grants.allow_groups` the groups are removed
   (`backend/open_webui/utils/access_control/__init__.py:276-299`).
3. **Open on anything but a shared chat.** "Anyone" grants are kept only where the item type has an
   Open permission (shared chats, `sharing.open_chats`); for every other item type they are removed
   on save, for admins too (`backend/open_webui/utils/access_control/__init__.py:239-251`;
   `backend/open_webui/routers/chats.py:2047-2053`).
4. **The group is not offered.** A non-admin only sees groups whose share setting lets them share to
   it (section 5.12).
5. **The recipient is pending.** Pending accounts cannot use anything, and "all users" listings
   exclude them (`backend/open_webui/models/access_grants.py:702-706`).
6. **The recipient cannot open that Workspace section.** A grant makes an item reachable; it does
   not grant the Workspace page. Without, for example, `workspace.knowledge`, the Workspace link and
   page are not available to the recipient (`src/lib/components/layout/Sidebar.svelte:164-172`;
   `src/routes/(app)/workspace/+layout.svelte:80-101`). Where the item can still be used (for
   example in chat) is covered by each item's reference document.
7. **A shared custom model sits on a base model the recipient cannot read.** The model appears in
   their list but use is refused with `Model not found`
   (`backend/open_webui/utils/models.py:563-570`;
   `backend/open_webui/utils/access_control/__init__.py:304-358`, `:405-409`; in chat
   `backend/open_webui/main.py:1149-1161` and `backend/open_webui/utils/models.py:517-521`).
8. **Group membership changed at sign-in.** SSO, LDAP or trusted-header group sync removed the
   recipient from the group the item was shared with (section 4, Group sync).
9. **The recipient's screen is out of date.** Server checks are current, but menus reflect the
   permissions loaded when the recipient's app started; a reload refreshes them (section 3.5).
10. **Files inside a shared knowledge base.** Sharing a knowledge base lets recipients read its
    files; write access to a file through a knowledge base applies only when the knowledge base's
    owner also owns the file (`backend/open_webui/utils/access_control/files.py:45-64`).
11. **The person or group was deleted.** Grants naming them remain but match no one (sections 5.4
    and 5.13).

How each sharing restriction is enforced on the server beyond what is described here is
security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

## 6. Data Model

Timestamps in these tables are epoch seconds. Table-level detail, migrations and indexes are in
`database-schema-identity-chats-and-config.md`; this section covers what support needs to reason
about roles, groups and sharing.

### 6.1 The `user` Table

`backend/open_webui/models/users.py:144-178`:

| Column | Meaning |
|---|---|
| `id` | Account id (a UUID for accounts created through `insert_new_auth`, `backend/open_webui/models/auths.py:118`) |
| `email` | Unique; stored in lower case by sign-up and admin paths |
| `username` | Optional handle, up to 50 characters |
| `role` | `admin`, `user` or `pending`; column default `pending` |
| `name` | Display name |
| `profile_image_url`, `profile_banner_image_url` | Avatar and banner; an empty avatar is replaced by `/api/v1/users/{user_id}/profile/image` when read (`:181`, `:223-227`) |
| `bio`, `gender`, `date_of_birth`, `timezone` | Profile fields; `timezone` comes from the browser |
| `presence_state`, `status_emoji`, `status_message`, `status_expires_at` | Presence and status (status endpoints need `users.enable_status`) |
| `info`, `variables`, `settings` | Free-form JSON; `settings.ui` holds personal interface settings; `variables` is never included in API responses (`:207`) |
| `oauth`, `scim` | Identity-provider links: `{provider: {"sub": ...}}` and `{provider: {"external_id": ...}}` (`:777-812`) |
| `last_active_at` | Last activity; drives "Last Active" and the green active dot (section 7.4) |
| `updated_at`, `created_at` | `created_at` also decides who the primary admin is |

Sign-in credentials live in the separate `auth` table keyed by the same id; see
`authentication-and-sign-in.md` (`backend/open_webui/models/auths.py:104-142`, `:228-239`).

### 6.2 The `group` and `group_member` Tables

| Table | Columns | Notes | Source |
|---|---|---|---|
| `group` | `id` (UUID), `user_id` (the admin or process that created it), `name`, `description`, `data` (JSON; `data.config.share` is the share setting), `meta` (JSON), `permissions` (JSON, same shape as Default permissions), `created_at`, `updated_at` | `updated_at` also changes when members are added or removed; group lists are ordered by it | `backend/open_webui/models/groups.py:37-52`, `:605-607`, `:177` |
| `group_member` | `id`, `group_id`, `user_id`, `created_at`, `updated_at` | One row per membership; unique on (`group_id`, `user_id`); both ids are declared with `ON DELETE CASCADE` in the migration; adding someone already in the group is ignored | `backend/open_webui/models/groups.py:73-86`, `:589-603`; `backend/open_webui/migrations/versions/37f288994c47_add_group_member_table.py:39-50` |

### 6.3 The `access_grant` Table

`backend/open_webui/models/access_grants.py:25-45`: `id`, `resource_type`, `resource_id`,
`principal_type` (`user`, `group` or `anyone`), `principal_id` (a user id, a group id, or `*`),
`permission` (`read` or `write`) and `created_at`, unique on the combination of the five descriptive
columns. The table has no foreign keys, so grants outlive a deleted user or group (sections 5.4 and
5.13).

How the grants read:

| Grant | Meaning |
|---|---|
| `user` / `*` / `read` | Public: every signed-in user can read |
| `user` / `*` / `write` | Public write: every signed-in user can edit |
| `user` / `{user id}` / `read` or `write` | One named person |
| `group` / `{group id}` / `read` or `write` | Every member of the group |
| `anyone` / `*` / `read` | Open: no sign-in needed (kept only for shared chats, section 5.17) |
| No grants | Private: only the owner (and admins when admin bypass is on) |

A grant answers only its own permission: a `write` check looks for a `write` grant and a `read`
check for a `read` grant (`backend/open_webui/models/access_grants.py:562-620`). The share panel
therefore adds both when **Write** is chosen (section 4, Read / Write). Older items stored access as
an `access_control` JSON value; the conversion rules (empty value means private, missing value
means public read except for files) are at `backend/open_webui/models/access_grants.py:83-147` and
`:276-318`.

### 6.4 Settings Rows

| Key in the `config` table | Holds | Seeded from | Source |
|---|---|---|---|
| `user.permissions` | The Default permissions object (all six sections) | `DEFAULT_USER_PERMISSIONS`, built from the `USER_PERMISSIONS_*` variables | `backend/open_webui/config.py:1940-2022`, `:3101` |
| `ui.default_user_role` | Role for new accounts | `DEFAULT_USER_ROLE` (`pending`) | `backend/open_webui/config.py:1720`, `:3096` |
| `ui.default_group_id` | Default Group id, or empty | `DEFAULT_GROUP_ID` (empty) | `backend/open_webui/config.py:1722`, `:3097` |
| `users.enable_status` | Whether status endpoints work | `ENABLE_USER_STATUS` (on) | `backend/open_webui/config.py:2052`, `:3119` |

After first boot the stored value wins over the environment variable (`../tools/ground-truth.md`,
Settings). Live values are data, TO BE CONFIRMED.

### 6.5 What Each Lookup Reveals About a Person

This matters for privacy questions and for interpreting screenshots.

| Lookup | Who may call it | Fields returned | Source |
|---|---|---|---|
| Admin user list `GET /api/v1/users/` | Admin | The whole user record except `variables` (including email, role, profile fields, timezone, personal settings, info, SSO and SCIM identifiers, activity times) plus group ids | `backend/open_webui/routers/users.py:82-126`; `backend/open_webui/models/users.py:184-219`, `:285-286` |
| One user `GET /api/v1/users/{user_id}` | Admin | As above plus group names and the active flag | `backend/open_webui/routers/users.py:785-811` |
| Search `GET /api/v1/users/search` | User | `id`, `name`, `email`, `role`, `bio`, status emoji, message and expiry. The response also has `groups` and `is_active` fields, but the search query returns plain user records without group or activity data, so they carry their defaults (an empty list and `false`) | `backend/open_webui/routers/users.py:137-161`; `backend/open_webui/models/users.py:303-316`, `:680-685` |
| Person info `GET /api/v1/users/{user_id}/info` | User | `id`, `name`, `email`, `role`, `bio`, status fields, the names and ids of the person's groups, and the active flag | `backend/open_webui/routers/users.py:814-832` |
| Active flag `GET /api/v1/users/{user_id}/active` | User | `active` true or false | `backend/open_webui/routers/users.py:901-907` |
| Groups list `GET /api/v1/groups/` | User | For non-admins, their own groups (or, with `share=true`, the groups they may share to): name, description, share setting, permissions, member count and creator id | `backend/open_webui/routers/groups.py:36-52`; `backend/open_webui/models/groups.py:102-103` |
| Group info `GET /api/v1/groups/id/{id}/info` | User | Name, description, creator id, member count, times | `backend/open_webui/routers/groups.py:116-128`; `backend/open_webui/models/groups.py:106-113` |

The search pages through every account, including pending ones and admins; the search text matches
any part of the name or email, ignoring letter case (`backend/open_webui/models/users.py:559-567`).
Search results are what the share pickers and channel mention lists show
(`src/lib/components/workspace/common/MemberSelector.svelte:61-77`;
`src/lib/components/channel/MessageInput/MentionList.svelte:61`).

## 7. Settings and Configuration

### 7.1 Where These Settings Live

- **Persistent settings** (`user.permissions`, `ui.default_user_role`, `ui.default_group_id`,
  `users.enable_status`) are rows in the `config` table. At first start they are seeded from the
  environment; afterwards the stored value wins and changing the environment variable has no effect
  (`../tools/ground-truth.md`, Settings; `backend/open_webui/models/config.py:240-266`).
- **Group permissions and share settings** are stored on each group row, not in `config`.
- **Environment-only switches** (`ENABLE_ADMIN_CHAT_ACCESS`, `BYPASS_ADMIN_ACCESS_CONTROL`,
  `BYPASS_MODEL_ACCESS_CONTROL`, `DEFAULT_GROUP_SHARE_PERMISSION`,
  `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL`, `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`,
  `ENABLE_PROFILE_IMAGE_URL_FORWARDING`, `PROFILE_IMAGE_ALLOWED_MIME_TYPES`) are read when the server
  starts; changing them needs a restart.
- All live values are data and are TO BE CONFIRMED for production.

### 7.2 Account and Group Settings

| Setting | Where an admin changes it | Key or variable | Code default | Effect | Source |
|---|---|---|---|---|---|
| Default User Role | Admin Settings › Authentication | `ui.default_user_role` (`DEFAULT_USER_ROLE`) | `pending` | Role for new accounts (section 5.15) | `backend/open_webui/config.py:1720`, `:3096` |
| Default Group | Admin Settings › Authentication | `ui.default_group_id` (`DEFAULT_GROUP_ID`) | empty (None) | Group new accounts join (section 5.15) | `backend/open_webui/config.py:1722`, `:3097` |
| Default permissions | Users › Groups › Default permissions | `user.permissions` (`USER_PERMISSIONS_*`) | section 7.5 | Baseline for every `user` | `backend/open_webui/config.py:1940-2022`, `:3101` |
| Share setting for new groups | Environment only | `DEFAULT_GROUP_SHARE_PERMISSION` | `members` | Initial **Who can share to this group** (`true`, `false` or `members`; anything else means No one) | `backend/open_webui/env.py:1023-1027`; `backend/open_webui/models/groups.py:137-145` |
| User Status | Admin Settings › General › **User Status** ("Show user status information in the app.") | `users.enable_status` (`ENABLE_USER_STATUS`) | on | When off, the status endpoints refuse with `The requested action has been restricted as a security measure.` | `backend/open_webui/config.py:2052`, `:3119`; `src/lib/components/admin/Settings/General.svelte:386-392`; `src/lib/i18n/locales/en-US/translation.json:2408-2409`; `backend/open_webui/routers/users.py:575-579`, `:596-600` |

### 7.3 Admin Visibility Switches

See section 3.7 for `ENABLE_ADMIN_CHAT_ACCESS` (on), `BYPASS_ADMIN_ACCESS_CONTROL` (on, falling back
to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) and `BYPASS_MODEL_ACCESS_CONTROL` (off). Related:
`ENABLE_ADMIN_EXPORT` (on) governs admin export features, documented in `admin-settings-panels.md`
(`backend/open_webui/config.py:2082`).

### 7.4 Activity and Profile Image Settings

| Variable | Code default | Effect | Source |
|---|---|---|---|
| Active window | 180 seconds (fixed in code) | A user counts as active when `last_active_at` is within the last 3 minutes; this drives the green dot in the Users table, the `is_active` flags and the active-user count | `backend/open_webui/models/users.py:901-925`; `src/lib/components/admin/Users/UserList.svelte:369-378` |
| `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL` | 60 seconds | `last_active_at` is written at most once per interval per user per server worker, on authenticated requests and on the browser's socket heartbeat; 0 or a negative value turns the limit off | `backend/open_webui/env.py:360-364`; `backend/open_webui/utils/misc.py:1158-1186`; `backend/open_webui/models/users.py:771-775`; `backend/open_webui/utils/auth.py:481-483`, `:563`; `backend/open_webui/socket/main.py:489-494` |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` | on | When on, every user's menu can show the number of active users; when off, only admins see it and others get `Access denied. Only administrators can view usage statistics.` from `/api/usage` | `backend/open_webui/env.py:367`; `backend/open_webui/main.py:2629-2637`; `src/lib/components/layout/Sidebar/UserMenu.svelte:89-93`, `:142-158` |
| `ENABLE_PROFILE_IMAGE_URL_FORWARDING` | on | When a profile image is an external web address, the avatar endpoint redirects to it; when off, the default avatar is shown instead | `backend/open_webui/env.py:970`; `backend/open_webui/routers/users.py:858-867` |
| `PROFILE_IMAGE_ALLOWED_MIME_TYPES` | `image/png,image/jpeg,image/gif,image/webp` | A stored image of another type is replaced by the default avatar when displayed | `backend/open_webui/env.py:971-977`; `backend/open_webui/routers/users.py:868-888` |

### 7.5 Every Permission Key

Labels are the switch names in the group and Default permissions editors
(`src/lib/components/admin/Users/Groups/Permissions.svelte`, line given in the Label column).
Defaults are the code defaults, which seed `user.permissions` at first start
(`backend/open_webui/config.py:1940-2022`); each variable is read with "true" meaning on. The
interface checks below are skipped for admins. Global feature switches that sit above some
permissions are listed in section 7.6.

**Workspace** (`backend/open_webui/config.py:1941-1955`; heading "Workspace Permissions",
`Permissions.svelte:44`)

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `workspace.models` | Models Access (`:49`) | off | `USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS` (`config.py:1733`) | Workspace › Models section and creating custom models (`src/routes/(app)/workspace/+layout.svelte:49`, `:82-83`; `backend/open_webui/routers/models.py:292-295`). Any Workspace "Access" key makes the Workspace link appear (`src/lib/components/layout/Sidebar.svelte:164-172`) |
| `workspace.models_import` | Import Models (`:58`) | off | `USER_PERMISSIONS_WORKSPACE_MODELS_IMPORT` (`:1753`) | **Import JSON** in Workspace › Models (`src/lib/components/workspace/Models.svelte:109-112`; `backend/open_webui/routers/models.py:449-451`) |
| `workspace.models_export` | Export Models (`:67`) | off | `USER_PERMISSIONS_WORKSPACE_MODELS_EXPORT` (`:1757`) | Model export options (`src/lib/components/workspace/Models.svelte:117-119`; `src/lib/components/workspace/Models/ModelMenu.svelte:173`; `backend/open_webui/routers/models.py:389-391`) |
| `workspace.knowledge` | Knowledge Access (`:87`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS` (`:1737`) | Workspace › Knowledge section and creating knowledge bases (`src/routes/(app)/workspace/+layout.svelte:50`, `:84-88`; `backend/open_webui/routers/knowledge.py:328-330`). No import or export switches exist for knowledge |
| `workspace.prompts` | Prompts Access (`:106`) | off | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS` (`:1741`) | Workspace › Prompts section and creating prompts (`src/routes/(app)/workspace/+layout.svelte:51`, `:89-93`; `backend/open_webui/routers/prompts.py:153`) |
| `workspace.prompts_import` | Import Prompts (`:115`) | off | `USER_PERMISSIONS_WORKSPACE_PROMPTS_IMPORT` (`:1761`) | Prompt import (`src/lib/components/workspace/Prompts.svelte:106`; `backend/open_webui/routers/prompts.py:158-160`) |
| `workspace.prompts_export` | Export Prompts (`:124`) | off | `USER_PERMISSIONS_WORKSPACE_PROMPTS_EXPORT` (`:1765`) | Prompt export (`src/lib/components/workspace/Prompts.svelte:124`; `src/lib/components/workspace/Prompts/PromptMenu.svelte:96`) |
| `workspace.tools` | Tools Access (`:151`) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS` (`:1745`) | Workspace › Tools section and creating or editing tool code; offered only when plugins are enabled. The editor warns `Warning: Enabling this will allow users to upload arbitrary code on the server.` (`Permissions.svelte:141-154`; `src/routes/(app)/workspace/+layout.svelte:53-55`, `:94-98`; `backend/open_webui/routers/tools.py:355`, `:520`) |
| `workspace.tools_import` | Import Tools (`:160`) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_IMPORT` (`:1769`) | Tool import (`src/lib/components/workspace/Tools.svelte:100`; `backend/open_webui/routers/tools.py:358`, `:521`) |
| `workspace.tools_export` | Export Tools (`:169`) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_EXPORT` (`:1773`) | Tool export (`src/lib/components/workspace/Tools.svelte:118`; `src/lib/components/workspace/Tools/ToolMenu.svelte:98`; `backend/open_webui/routers/tools.py:323-325`) |
| `workspace.skills` | Skills Access (`:196`) | off | `USER_PERMISSIONS_WORKSPACE_SKILLS_ACCESS` (`:1749`) | Workspace › Skills section and creating skills; carries the same code warning (`Permissions.svelte:187-199`; `src/routes/(app)/workspace/+layout.svelte:52`, `:99-100`; `backend/open_webui/routers/skills.py:159-161`) |
| `workspace.skills_import` | Import Skills (`:205`) | off | `USER_PERMISSIONS_WORKSPACE_SKILLS_IMPORT` (`:1777`) | Skill import (`src/lib/components/workspace/Skills.svelte:85`; `backend/open_webui/routers/skills.py:160`) |
| `workspace.skills_export` | Export Skills (`:214`) | off | `USER_PERMISSIONS_WORKSPACE_SKILLS_EXPORT` (`:1781`) | Skill export (`src/lib/components/workspace/Skills.svelte:102`; `src/lib/components/workspace/Skills/SkillMenu.svelte:78`; `backend/open_webui/routers/skills.py:130-132`) |

**Sharing** (`backend/open_webui/config.py:1956-1973`; heading "Sharing Permissions",
`Permissions.svelte:235`). The non-public keys decide whether the share panel shows its Access
List; the public keys decide whether **Public** is offered and kept (section 5.16).

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `sharing.models` | Models Sharing (`:240`) | off | `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_SHARING` (`:1786`) | Access List in a model's Access dialog (`src/lib/components/workspace/Models/ModelEditor.svelte:604`) |
| `sharing.public_models` | Models Public Sharing (`:257`) | off | `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING` (`:1790`) | **Public** for models (`ModelEditor.svelte:605`; `backend/open_webui/routers/models.py:347-352`) |
| `sharing.knowledge` | Knowledge Sharing (`:277`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_SHARING` (`:1794`) | Access List for knowledge bases (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1223`) |
| `sharing.public_knowledge` | Knowledge Public Sharing (`:297`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING` (`:1798`) | **Public** for knowledge bases (`KnowledgeBase.svelte:1224`; `backend/open_webui/routers/knowledge.py:336-341`) |
| `sharing.prompts` | Prompts Sharing (`:317`) | off | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_SHARING` (`:1802`) | Access List for prompts (`src/lib/components/workspace/Prompts/PromptEditor.svelte:299`) |
| `sharing.public_prompts` | Prompts Public Sharing (`:334`) | off | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING` (`:1806`) | **Public** for prompts (`PromptEditor.svelte:300`; `backend/open_webui/routers/prompts.py:169-174`) |
| `sharing.tools` | Tools Sharing (`:354`) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_SHARING` (`:1811`) | Access List for tools (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:211`) |
| `sharing.public_tools` | Tools Public Sharing (`:371`) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING` (`:1815`) | **Public** for tools (`ToolkitEditor.svelte:212`; `backend/open_webui/routers/tools.py:379-384`) |
| `sharing.skills` | Skills Sharing (`:391`) | off | `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_SHARING` (`:1819`) | Access List for skills (`src/lib/components/workspace/Skills/SkillEditor.svelte:97`) |
| `sharing.public_skills` | Skills Public Sharing (`:408`) | off | `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_PUBLIC_SHARING` (`:1823`) | **Public** for skills (`SkillEditor.svelte:98`; `backend/open_webui/routers/skills.py:188-193`) |
| `sharing.notes` | Notes Sharing (`:428`) | off | `USER_PERMISSIONS_NOTES_ALLOW_SHARING` (`:1828`) | Access List for notes (`src/lib/components/notes/NoteEditor.svelte:996`) |
| `sharing.public_notes` | Notes Public Sharing (`:445`) | off | `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING` (`:1830`) | **Public** for notes (`NoteEditor.svelte:997`; `backend/open_webui/routers/notes.py:221-226`) |
| `sharing.folders` | Folders Sharing (`:465`) | off | `USER_PERMISSIONS_FOLDERS_ALLOW_SHARING` (`:1834`) | Access List in a folder's share dialog; folders have no Public option (`src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:79-80`) |
| `sharing.public_chats` | Chats Public Sharing (`:482`) | off | `USER_PERMISSIONS_CHAT_ALLOW_PUBLIC_SHARING` (`:1877`) | **Public** for a shared chat's access; switch shown only under Allow Chat Share (`Permissions.svelte:478`; `src/lib/components/chat/ShareChatModal.svelte:163`; `backend/open_webui/routers/chats.py:2047-2052`) |
| `sharing.open_chats` | Chats Open Sharing (`:501`) | off | `USER_PERMISSIONS_CHAT_ALLOW_OPEN_SHARING` (`:1881`) | **Open** ("Anyone with the link can view") for a shared chat (`ShareChatModal.svelte:164`; `backend/open_webui/routers/chats.py:2053`) |
| `sharing.public_calendars` | Calendars Public Sharing (`:522`) | off | `USER_PERMISSIONS_CALENDAR_ALLOW_PUBLIC_SHARING` (`:1837`) | Public grants on calendars; switch shown only under Calendar (`Permissions.svelte:518`; `backend/open_webui/routers/calendar.py:120-125`, `:420-425`) |

**Access grants** (`backend/open_webui/config.py:1974-1977`; heading "Access Grants",
`Permissions.svelte:543`)

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `access_grants.allow_users` | Allow Sharing With Users (`:548`) | on | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS` (`:1841`) | Picking individual people in every share panel; named people are removed on save without it (`src/lib/components/workspace/common/AccessControl.svelte:644`; `backend/open_webui/utils/access_control/__init__.py:276-283`) |
| `access_grants.allow_groups` | Allow Sharing With Groups (`:567`) | on | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_GROUPS` (`:1844`) | Picking groups in every share panel; groups are removed on save without it (`src/lib/components/workspace/common/AddAccessModal.svelte:60`; `backend/open_webui/utils/access_control/__init__.py:285-299`) |

**Chat** (`backend/open_webui/config.py:1978-2000`; heading "Chat Permissions",
`Permissions.svelte:587`)

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `chat.file_upload` | Allow File Upload (`:592`) | on | `USER_PERMISSIONS_CHAT_FILE_UPLOAD` (`:1857`) | Uploading files in the chat input; refused uploads show `You do not have permission to upload files.`; also knowledge uploads in the model editor and file-reading built-in tools (`src/lib/components/chat/MessageInput.svelte:918-921`; `src/lib/components/chat/MessageInput/InputMenu.svelte:68-70`; `src/lib/components/workspace/Models/Knowledge.svelte:38-39`, `:208`; `backend/open_webui/utils/tools.py:594-600`) |
| `chat.web_upload` | Allow Web Upload (`:611`) | on | `USER_PERMISSIONS_CHAT_WEB_UPLOAD` (`:1859`) | Attaching web pages; refusal shows `You do not have permission to upload web content.` (`src/lib/components/chat/MessageInput/InputMenu.svelte:72-73`; `src/lib/components/chat/Chat.svelte:1790-1793`) |
| `chat.controls` | Allow Chat Controls (`:627`) | on | `USER_PERMISSIONS_CHAT_CONTROLS` (`:1849`) | The **Controls** button and panel in a chat; with the next two keys it also decides whether a personal system prompt and parameters can be saved (`src/lib/components/chat/Navbar.svelte:246`; `src/lib/components/chat/ChatControls.svelte:65`; `src/lib/components/chat/Controls/Controls.svelte:56`; `backend/open_webui/routers/users.py:500-518`) |
| `chat.valves` | Allow Chat Valves (`:644`) | on | `USER_PERMISSIONS_CHAT_VALVES` (`:1851`) | User valves of tools and functions in a chat (`src/lib/components/chat/Controls/Controls.svelte:94`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:415`, `:625`; `src/lib/components/chat/MessageInput.svelte:2427-2429`) |
| `chat.system_prompt` | Allow Chat System Prompt (`:660`) | on | `USER_PERMISSIONS_CHAT_SYSTEM_PROMPT` (`:1853`) | System prompt in chat Controls, in folder settings and in Settings › General; the server drops a saved `system` setting without it (`src/lib/components/chat/Controls/Controls.svelte:109`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:216`; `src/lib/utils/settings-access.ts:3-5`; `backend/open_webui/routers/users.py:500-508`) |
| `chat.params` | Allow Chat Params (`:679`) | on | `USER_PERMISSIONS_CHAT_PARAMS` (`:1855`) | Advanced parameters in chat Controls and Settings; the server drops saved `params` without it (`src/lib/components/chat/Controls/Controls.svelte:131`; `src/lib/utils/settings-access.ts:6-8`; `backend/open_webui/routers/users.py:510-518`) |
| `chat.edit` | Allow Chat Edit (`:696`) | on | `USER_PERMISSIONS_CHAT_EDIT` (`:1873`) | The edit button on model responses (`src/lib/components/chat/Messages/ResponseMessage.svelte:1087`) |
| `chat.delete` | Allow Chat Delete (`:712`) | on | `USER_PERMISSIONS_CHAT_DELETE` (`:1861`) | Deleting chats from the sidebar, menus, search, archive and Data Controls (`src/lib/components/layout/Sidebar/ChatItem.svelte:731`; `src/lib/components/layout/Sidebar/ChatMenu.svelte:466`; `src/lib/components/chat/Navbar.svelte:153`; `src/lib/utils/settings-access.ts:49`; `backend/open_webui/routers/chats.py:713`, `:1580`; `backend/open_webui/routers/folders.py:699-702`) |
| `chat.delete_message` | Allow Delete Messages (`:728`) | on | `USER_PERMISSIONS_CHAT_DELETE_MESSAGE` (`:1863`) | Delete buttons on messages (`src/lib/components/chat/Messages/UserMessage.svelte:593`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1583`) |
| `chat.continue_response` | Allow Continue Response (`:747`) | on | `USER_PERMISSIONS_CHAT_CONTINUE_RESPONSE` (`:1865`) | Continue button on the last response (`ResponseMessage.svelte:1357`) |
| `chat.regenerate_response` | Allow Regenerate Response (`:766`) | on | `USER_PERMISSIONS_CHAT_REGENERATE_RESPONSE` (`:1867`) | Regenerate button (`ResponseMessage.svelte:1394`) |
| `chat.rate_response` | Allow Rate Response (`:785`) | on | `USER_PERMISSIONS_CHAT_RATE_RESPONSE` (`:1871`) | Rating buttons, when message rating is enabled (`ResponseMessage.svelte:1279`) |
| `chat.share` | Allow Chat Share (`:804`) | on | `USER_PERMISSIONS_CHAT_SHARE` (`:1875`) | **Share** in chat menus; the server refuses sharing without it (`ChatMenu.svelte:311`; `src/lib/components/layout/Navbar/Menu.svelte:368`; `backend/open_webui/routers/chats.py:1951-1953`) |
| `chat.export` | Allow Chat Export (`:820`) | on | `USER_PERMISSIONS_CHAT_EXPORT` (`:1885`) | Download and export options for chats (`ChatMenu.svelte:324`; `src/lib/components/layout/Navbar/Menu.svelte:382`; `src/lib/utils/settings-access.ts:47-48`) |
| `chat.import` | Allow Chat Import (`:836`) | on | `USER_PERMISSIONS_CHAT_IMPORT` (`:1887`) | Importing chats, cloning a chat or a shared chat, and forking from a response; a refused clone shows `Access prohibited` (`src/lib/components/layout/Sidebar.svelte:42`; `src/lib/components/layout/Sidebar/ChatItem.svelte:224-226`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1552`; `src/routes/s/[id]/+page.svelte:46-48`; `backend/open_webui/routers/chats.py:231-235`, `:1841`) |
| `chat.stt` | Allow Speech to Text (`:852`) | on | `USER_PERMISSIONS_CHAT_STT` (`:1889`) | Dictation button; the server refuses transcription without it (`src/lib/components/chat/MessageInput.svelte:2630`; `backend/open_webui/routers/audio.py:1258-1262`) |
| `chat.tts` | Allow Text to Speech (`:868`) | on | `USER_PERMISSIONS_CHAT_TTS` (`:1891`) | Read-aloud on responses; the server refuses speech without it (`ResponseMessage.svelte:1146`; `backend/open_webui/routers/audio.py:612-616`) |
| `chat.call` | Allow Call (`:884`) | on | `USER_PERMISSIONS_CHAT_CALL` (`:1893`) | Voice call button (`src/lib/components/chat/MessageInput.svelte:2671`) |
| `chat.multiple_models` | Allow Multiple Models in Chat (`:900`) | on | `USER_PERMISSIONS_CHAT_MULTIPLE_MODELS` (`:1895`) | Adding more than one model; without it a chat keeps only its first model (`src/lib/components/chat/ModelSelector.svelte:83-84`; `src/lib/components/chat/Chat.svelte:2323-2324`) |
| `chat.temporary` | Allow Temporary Chat (`:919`) | on | `USER_PERMISSIONS_CHAT_TEMPORARY` (`:1897`) | Temporary-chat toggle, the `?temporary-chat=true` link and the "temporary chat by default" setting (`src/lib/components/chat/Navbar.svelte:180`; `src/routes/(app)/+layout.svelte:359-362`; `src/lib/components/chat/Chat.svelte:2042-2043`; `src/lib/utils/settings-access.ts:19-20`) |
| `chat.temporary_enforced` | Enforce Temporary Chat (`:939`) | off | `USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED` (`:1899`) | Forces every chat to be temporary for users and hides the toggle; switch shown only under Allow Temporary Chat (`Permissions.svelte:935`; `src/lib/components/chat/Chat.svelte:2025-2026`; `src/routes/(app)/+layout.svelte:364-365`; `src/lib/components/layout/Sidebar.svelte:818`) |

**Features** (`backend/open_webui/config.py:2001-2016`; heading "Features Permissions",
`Permissions.svelte:960`). Built-in tools offered to models are filtered by these keys too
(`backend/open_webui/utils/tools.py:558-566`).

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `features.api_keys` | API Keys (`:965`) | off | `USER_PERMISSIONS_FEATURES_API_KEYS` (`:1924`) | API key section of Settings › Account; creation is refused without it (`src/lib/components/chat/Settings/Account.svelte:226-230`; `backend/open_webui/routers/auths.py:1517-1525`) |
| `features.notes` | Notes (`:981`) | on | `USER_PERMISSIONS_FEATURES_NOTES` (`:1920`) | Notes in the sidebar and user menu and the `/notes` pages (`src/lib/components/layout/Sidebar.svelte:160-162`; `src/routes/(app)/notes/+layout.svelte:11-17`; `backend/open_webui/routers/notes.py:72`) |
| `features.channels` | Channels (`:997`) | on | `USER_PERMISSIONS_FEATURES_CHANNELS` (`:1922`) | Channels in the sidebar (`Sidebar.svelte:1330-1336`; `backend/open_webui/routers/channels.py:149-156`) |
| `features.folders` | Folders (`:1013`) | on | `USER_PERMISSIONS_FEATURES_FOLDERS` (`:1918`) | Chat folders in the sidebar (`Sidebar.svelte:1363`; `backend/open_webui/routers/folders.py:74-80`) |
| `features.direct_tool_servers` | Direct Tool Servers (`:1029`) | off | `USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS` (`:1904`) | A user's own tool servers in Settings and the terminal selector; without it saved tool servers are dropped and ignored (`src/lib/components/chat/SettingsModal.svelte:387-389`, `:639`; `src/lib/components/chat/MessageInput.svelte:802-803`; `backend/open_webui/routers/users.py:520-530`; `backend/open_webui/main.py:1244-1251`) |
| `features.web_search` | Web Search (`:1048`) | on | `USER_PERMISSIONS_FEATURES_WEB_SEARCH` (`:1908`) | Web search toggle in the chat input (`src/lib/components/chat/MessageInput.svelte:826-828`; `src/lib/components/chat/Chat.svelte:349-351`) |
| `features.image_generation` | Image Generation (`:1064`) | on | `USER_PERMISSIONS_FEATURES_IMAGE_GENERATION` (`:1910`) | Image generation toggle (`MessageInput.svelte:832-834`; `backend/open_webui/routers/images.py:572`) |
| `features.code_interpreter` | Code Interpreter (`:1083`) | on | `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` (`:1914`) | Code interpreter toggle (`MessageInput.svelte:839-841`; `backend/open_webui/utils/middleware.py:4887`) |
| `features.memories` | Memories (`:1102`) | on | `USER_PERMISSIONS_FEATURES_MEMORIES` (`:1926`) | Settings › Personalization (memories) (`SettingsModal.svelte:397-400`; `backend/open_webui/routers/memories.py:43`) |
| `features.automations` | Automations (`:1124`) | off | `USER_PERMISSIONS_FEATURES_AUTOMATIONS` (`:1928`) | Automations link and pages; the editor warns `Warning: Enabling this will allow users to run scheduled prompts automatically.` (`Permissions.svelte:1116-1127`; `Sidebar.svelte:173-176`; `src/routes/(app)/automations/+layout.svelte:56-62`; `backend/open_webui/routers/automations.py:51-58`) |
| `features.calendar` | Calendar (`:1140`) | on | `USER_PERMISSIONS_FEATURES_CALENDAR` (`:1930`) | Calendar link and pages (`Sidebar.svelte:178-181`; `backend/open_webui/routers/calendar.py:45-49`) |
| `features.webhooks` | User Webhooks (`:1156`) | off | `USER_PERMISSIONS_FEATURES_USER_WEBHOOKS` (`:1932`) | Personal notification targets (webhooks) in Settings › Notifications; without it a saved webhook URL is dropped (`src/lib/utils/settings-access.ts:16-18`, `:51-55`; `backend/open_webui/routers/users.py:532-547`) |

**Settings** (`backend/open_webui/config.py:2017-2019`; heading "Settings Permissions",
`Permissions.svelte:1173`)

| Key | Label | Default | Variable | What it controls |
|---|---|---|---|---|
| `settings.interface` | Interface Settings Access (`:1178`) | on | `USER_PERMISSIONS_SETTINGS_INTERFACE` (`:1937`) | The Settings › Interface tab; without it the server discards changes to Interface fields, including the fork's Hide Processing Details and Inline Citations (`src/lib/components/chat/SettingsModal.svelte:393-394`; `backend/open_webui/routers/users.py:493-498`; `backend/open_webui/models/users.py:67-135`) |

That is 65 keys: 13 workspace, 16 sharing, 2 access grants, 21 chat, 12 features and 1 settings
(`backend/open_webui/routers/users.py:193-285`). One further key, `sharing.public_channels`, is
checked when channels are saved but is not in the defaults or the editor, so for non-admins public
channel grants are removed on save (`backend/open_webui/routers/channels.py:312-318`, `:726-732`).

### 7.6 Global Switches Above the Permissions

A permission only matters when the feature itself is switched on for the whole site. These switches
are documented in `admin-settings-panels.md` and the configuration catalogues.

| Feature | Global switch (key; variable) | Code default | Permission it gates | Source |
|---|---|---|---|---|
| Notes | `notes.enable`; `ENABLE_NOTES` | on | `features.notes`, `sharing.notes`, `sharing.public_notes` | `backend/open_webui/config.py:2050`; `src/lib/components/layout/Sidebar.svelte:161` |
| Channels | `channels.enable`; `ENABLE_CHANNELS` | **off** | `features.channels` | `backend/open_webui/config.py:2028`; `src/lib/components/layout/Sidebar.svelte:1330` |
| Folders | `folders.enable`; `ENABLE_FOLDERS` | on | `features.folders` | `backend/open_webui/config.py:2024`; `src/lib/components/layout/Sidebar.svelte:1363` |
| Calendar | `calendar.enable`; `ENABLE_CALENDAR` | on | `features.calendar` | `backend/open_webui/config.py:2032`; `src/lib/components/layout/Sidebar.svelte:180` |
| Automations | `automations.enable`; `ENABLE_AUTOMATIONS` | on | `features.automations` | `backend/open_webui/config.py:2034`; `src/lib/components/layout/Sidebar.svelte:175` |
| User webhooks | `ui.enable_user_webhooks`; `ENABLE_USER_WEBHOOKS` | **off** | `features.webhooks` | `backend/open_webui/config.py:2100`; `src/lib/utils/settings-access.ts:16-18` |
| API keys | `auth.enable_api_keys`; `ENABLE_API_KEYS` | **off** | `features.api_keys` | `backend/open_webui/config.py:2454`; `src/lib/utils/settings-access.ts:13-15` |
| Web search | `web.search.enable`; `ENABLE_WEB_SEARCH` | **off** | `features.web_search` | `backend/open_webui/config.py:1161`, `:2941`; `src/lib/components/chat/MessageInput.svelte:827` |
| Image generation | `image_generation.enable`; `ENABLE_IMAGE_GENERATION` | **off** | `features.image_generation` | `backend/open_webui/config.py:1351`, `:3019`; `src/lib/components/chat/MessageInput.svelte:833` |
| Code interpreter | `code_interpreter.enable`; `ENABLE_CODE_INTERPRETER` | on | `features.code_interpreter` | `backend/open_webui/config.py:424`, `:2843`; `src/lib/components/chat/MessageInput.svelte:840` |
| Memories | `memories.enable`; `ENABLE_MEMORIES` | on | `features.memories` | `backend/open_webui/config.py:426`, `:2844`; `src/lib/components/chat/SettingsModal.svelte:399` |
| Direct integrations | `direct.integrations.enable`; `ENABLE_DIRECT_INTEGRATIONS` | **off** | `features.direct_tool_servers` | `backend/open_webui/config.py:231`, `:2824`; `src/lib/components/chat/SettingsModal.svelte:387` |
| Plugins | `ENABLE_PLUGINS` (environment only) | on | `workspace.tools` | `backend/open_webui/env.py:1186`; `src/routes/(app)/workspace/+layout.svelte:53-55` |
| Message rating | `ui.enable_message_rating`; `ENABLE_MESSAGE_RATING` | on | `chat.rate_response` | `backend/open_webui/config.py:2098`, `:3124`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1279` |

## 8. Cron Jobs and Background Processes

Nothing in this area runs on a schedule; there is no crontab (`../tools/ground-truth.md`). What
happens without a click:

| What | When | Detail | Source |
|---|---|---|---|
| Activity time-stamp | On authenticated requests and on the browser's socket heartbeat | `last_active_at` is updated at most once per `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL` (60 seconds) per user per server worker. On requests the write runs as a separate background task so the request does not wait | `backend/open_webui/utils/auth.py:481-483`; `backend/open_webui/socket/main.py:489-494`; `backend/open_webui/models/users.py:771-775` |
| Default group assignment | At account creation (save time) | New accounts are added to the Default Group; a failure is only logged as `Failed to add user {user_id} to default group {default_group_id}: {e}` | `backend/open_webui/utils/groups.py:8-24` |
| Group sync | At each SSO, LDAP or trusted-header sign-in, when group management is on | Memberships are replaced to match the identity provider; SSO sync can also store a copy of the Default permissions on a group whose permissions are empty | `backend/open_webui/models/groups.py:516-572`; `backend/open_webui/utils/oauth.py:1730-1800`; `backend/open_webui/routers/auths.py:693-702`, `:768`; detail in `sso-oauth-oidc-and-scim.md` |
| Socket disconnect | Immediately after a role change or a deletion is saved | The person's live connections are closed so the browser reconnects with fresh data | `backend/open_webui/events.py:1089-1100`; `backend/open_webui/socket/main.py:388-404` |
| Event delivery | Immediately after each user or group change | Each event is handed to the event sinks (socket sessions, event functions, event webhooks, notifications); webhook and notification deliveries run as background tasks | `backend/open_webui/events.py:1062-1086`, `:1171-1202` |

Effective permissions are not cached: each server check reads the user's groups and the
`user.permissions` setting at the time of the request
(`backend/open_webui/utils/access_control/__init__.py:97-108`; `backend/open_webui/models/config.py:141-147`). The interface's copy is refreshed
only when the app reloads the session (section 3.5).

## 9. Notifications and Emails

- **No email.** The application has no mail-sending code (`../tools/ground-truth.md`, Contacts). A
  person is not emailed when their account is approved, their role changes, they are added to a
  group or their account is deleted.
- **No in-app notification to the affected person.** The in-app and browser notification system
  only handles chat completion and failure, channel messages, calendar alerts and failed document
  processing (`backend/open_webui/events.py:669-675`); none of the user or group events below are
  among them. A pending person sees their approval only by pressing **Check Again** or reloading
  (`src/lib/components/layout/Overlay/AccountPending.svelte:59-67`).
- **Live connections.** A role change or a deletion closes that person's socket connections; the
  browser reconnects (`backend/open_webui/events.py:1089-1100`;
  `backend/open_webui/socket/main.py:388-404`). This refreshes server-side session data; it does
  not by itself redraw their screen.
- **Event webhooks and event functions.** Every change in this area publishes an event. If an
  administrator has configured event webhooks (Admin Settings › Events, setting `events.webhooks`;
  detail in `notifications-webhooks-events-and-banners.md`), each matching webhook receives a message
  of the form `{message} ({subject id})` plus the event body, which names the acting user by id,
  name, email and role (`backend/open_webui/events.py:704`, `:1034-1059`). A legacy single webhook
  URL is converted into a webhook that receives **all** events (`backend/open_webui/events.py:854-878`).
  Event-type functions also receive events when plugins are enabled
  (`backend/open_webui/events.py:1103-1107`, `:1171`).

Events published by this area, with the message a webhook receives
(`backend/open_webui/events.py:108-160`):

| Event | Webhook message | Published when | Source |
|---|---|---|---|
| `user.created` | `User created` | An admin adds a user (form or CSV); other creation paths are in `authentication-and-sign-in.md` | `backend/open_webui/routers/auths.py:1137-1144` |
| `user.updated` | `User updated` | An admin changes name, email or profile image (the event lists the changed fields) | `backend/open_webui/routers/users.py:997-1004` |
| `user.role_updated` | `User role updated` | An admin changes a role | `backend/open_webui/routers/users.py:1006-1013` |
| `auth.password_changed` | `Password changed` | An admin sets a new password in Edit User (source `admin`) | `backend/open_webui/routers/users.py:1015-1023` |
| `user.deleted` | `User deleted` | An admin deletes a user | `backend/open_webui/routers/users.py:1066-1072` |
| `user.permissions_updated` | `User permissions updated` | Default permissions are saved | `backend/open_webui/routers/users.py:428-434` |
| `user.settings_updated` | `User settings updated` | A person saves their own settings | `backend/open_webui/routers/users.py:549-556` |
| `user.status_updated` | `User status updated` | A person saves their status | `backend/open_webui/routers/users.py:602-609` |
| `group.created` | `Group created` | A group is created (also by SSO group creation) | `backend/open_webui/routers/groups.py:68-76`; `backend/open_webui/utils/oauth.py:1708-1714` |
| `group.updated` | `Group updated` | A group is saved | `backend/open_webui/routers/groups.py:189-197` |
| `group.deleted` | `Group deleted` | A group is deleted | `backend/open_webui/routers/groups.py:309-316` |
| `group.member_added` | `Group member added` | Members are added (by an admin or by SSO sync) | `backend/open_webui/routers/groups.py:234-242`; `backend/open_webui/utils/oauth.py:1776-1784` |
| `group.member_removed` | `Group member removed` | Members are removed (by an admin or by SSO sync) | `backend/open_webui/routers/groups.py:271-279`; `backend/open_webui/utils/oauth.py:1739-1747` |

The constant `New user signed up: {username}` exists in `backend/open_webui/constants.py:34`, but no
code in `backend/open_webui` sends it.

## 10. Error, Warning and Notice Messages (Verbatim)

Interpolated values are written as `{name}`. Most pages in this area print a server refusal as a
pop-up containing the server's text unchanged (for example
`src/lib/components/admin/Users/UserList.svelte:59-63`,
`src/lib/components/admin/Users/UserList/EditUserModal.svelte:46-49`,
`src/lib/components/admin/Users/Groups/GroupItem.svelte:29-33`), so the backend rows below are what
admins see in those pop-ups. All plain-key English text below is the key itself
(`src/lib/i18n/locales/en-US/translation.json` holds empty values for them). Rows marked "Log" are
server log lines, not user messages; several contain user ids, which are personal data.

### 10.1 Backend Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:570-575`, `:625-631`; `backend/open_webui/routers/chats.py:748-749` | A pending account calls any user endpoint; a non-admin calls an admin endpoint; an admin lists a user's chats while `ENABLE_ADMIN_CHAT_ACCESS` is off | Pending users wait for approval; others ask an admin | Check the person's role in Users › Overview; for the chats case, the live `ENABLE_ADMIN_CHAT_ACCESS` value (TO BE CONFIRMED) |
| `We could not find what you're looking for :/` | Error (HTTP 400; 404 for the preview) | `backend/open_webui/routers/users.py:559-562`, `:611-614`, `:667-670`, `:694-697`, `:808-811`, `:829-832`, `:843-846`, `:890-893`, `:1031-1034`, `:1113-1116` | The user id no longer exists (deleted, or the page is stale); for the SSO-sessions lookup, also when the user simply has no SSO sessions | Reload the Users list | Confirm the account still exists; note the time of any deletion |
| `We could not find what you're looking for :/` | Error (HTTP 401; 404 for the preview) | `backend/open_webui/routers/groups.py:110-113`, `:125-128`, `:151-154`, `:347-350` | The group id no longer exists | Reload the Groups list | Confirm the group still exists; share panels quietly omit groups they cannot look up (`src/lib/components/workspace/common/AccessControl.svelte:385-400`) |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403) | `backend/open_webui/routers/users.py:930-933`, `:937-940`, `:1050-1053`, `:1081-1084` | Another admin edits the primary admin; the primary admin changes their own role; anyone deletes the primary admin; an admin deletes their own account | None for the requester; the action is not allowed | Section 3.3. Identify which account is the primary admin (earliest created) |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403) | `backend/open_webui/routers/users.py:575-579`, `:596-600` | Reading or saving a status while **User Status** (`users.enable_status`) is off | None | Live value of `users.enable_status` (TO BE CONFIRMED) |
| `Could not verify primary admin status.` | Error (HTTP 500) | `backend/open_webui/routers/users.py:946-949`, `:1058-1061` | The primary-admin lookup failed while saving or deleting a user | Try again later | Server log line `Error checking primary admin status: {e}`; escalate with the time |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400) | `backend/open_webui/routers/users.py:954-960` | An admin changes a user's email to one another account uses (comparison ignores letter case) | Use a different email or find the existing account | Search Users › Overview for the email |
| `{e}` (password rule text, for example `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` or `The password does not meet the required validation criteria.`) | Error (HTTP 400) | `backend/open_webui/routers/users.py:962-966`; `backend/open_webui/utils/auth.py:190-201`; `backend/open_webui/constants.py:48-50`, `:114` | The admin-set password breaks a password rule | Choose a password that meets the rules | Rules and hint text are in `authentication-and-sign-in.md` |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/users.py:1026-1029`; `backend/open_webui/constants.py:16-18` | The user record could not be re-read after an edit | Reload and check whether the change was saved | Escalate with the time and the user's email |
| `Oops! Something went wrong. We encountered an issue while trying to delete the user. Please give it another shot.` | Error (HTTP 500) | `backend/open_webui/routers/users.py:1075-1078` | Deleting the user's chats or rows failed | Do not retry repeatedly; report it | The person may already be out of their groups (section 5.4); escalate with the time |
| `start_date must be before end_date` | Error (HTTP 400) | `backend/open_webui/routers/users.py:722-726` | A usage request (Settings › Usage) with a start after its end | Pick a valid date range | None |
| `{exc}` (chat variable validation text) | Error (HTTP 400) | `backend/open_webui/routers/users.py:657-663` | Saving personal chat variables that fail validation | Correct the variables | Messages are in `user-settings-and-personalisation.md` |
| `[ERROR: Error creating group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:81-85`, `:88-93` | The group could not be stored | Try again; report if repeated | Log line `Error creating a new group: {e}` |
| `[ERROR: Error getting group members]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:164-172` | Listing a group's members through the API failed (no interface caller) | None | Log line (it reads `Error adding users to group {id}: {e}`) |
| `[ERROR: Error updating group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:202-206`, `:209-214` | Saving the group failed | Try again; report if repeated | Log line `Error updating group {id}: {e}` |
| `[ERROR: Error adding users to group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:247-251`, `:254-259` | Adding members failed, for example because the group no longer exists | Reload the group | Log line `Error adding users to group {id}: {e}` |
| `[ERROR: Error removing users from group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:284-288`, `:291-296` | Removing members failed | Reload the group | Log line `Error removing users from group {id}: {e}` |
| `[ERROR: Error deleting group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:318-322`, `:325-330` | Deleting the group failed | Try again; report if repeated | Log line `Error deleting group {id}: {e}` |
| `The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com).` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1109-1110` | Add User or a CSV row has a malformed email | Fix the address | Check the CSV line named in the pop-up |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1112-1113` | Add User or a CSV row uses an email that already has an account | Skip or change that row | Search Users › Overview for the email |
| `{e}` (password rule text) | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1115-1119` | Add User or a CSV row has a password that breaks a rule | Choose a compliant password | `authentication-and-sign-in.md` |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1157-1158` | The account rows were not created | Try again later | Escalate with the time |
| `An internal error occurred while adding the user.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1159-1163` | Unexpected failure while adding a user | Try again later | Log line `Add user error: {err}`; escalate |
| `Model not found` | Error (HTTP 403; HTTP 400 when sending a chat or pressing a message action button; inside the response when the check just before sending fails) | `backend/open_webui/utils/access_control/__init__.py:405`, `:409`, `:413`; `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521`; `backend/open_webui/main.py:1640-1645`; chat path `backend/open_webui/main.py:1128-1129`, `:1149-1161`, `:1180-1182`, `:1686-1710`, `backend/open_webui/utils/chat.py:198-203`; message actions `backend/open_webui/utils/actions.py:58-59`, `backend/open_webui/main.py:2121-2125` | A non-admin uses a model they cannot read, a custom model whose base model they cannot read, or an unregistered base model (in chat, also an admin while `BYPASS_ADMIN_ACCESS_CONTROL` is off). For everyone, admins included: the model is not in the server's current model list, or a custom model's base model is not currently offered by any connection and no fallback applies (section 3.7, steps 1 and 3) | Ask the model's owner or an admin to share it, or pick another model; if colleagues and admins get the same refusal, report it as an availability problem | Section 3.7 and `workspace-models-and-model-access.md`; log lines below. A chat refusal is also logged as `Error processing chat metadata: Model not found` (HTTP refusal) or `Error processing chat payload: Model not found` (inside the response), preceded by a `Model access denied` line only when access, not availability, was the cause (`backend/open_webui/main.py:1641`, `:1688`) |
| `Access denied. Only administrators can view usage statistics.` | Error (HTTP 403) | `backend/open_webui/main.py:2629-2632` | A non-admin asks for the active-user count while `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off | None | None |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:455-460` | The signed-in account no longer exists (for example it was deleted) | Sign in again; a deleted account cannot | Check whether the account was deleted |
| `Error checking primary admin status: {e}` | Log (error) | `backend/open_webui/routers/users.py:945`, `:1057` | See `Could not verify primary admin status.` | n/a | Send the time to the platform maintainer |
| `Error creating a new group: {e}` | Log (exception) | `backend/open_webui/routers/groups.py:89` | Group creation failed | n/a | As above |
| `Error adding users to group {id}: {e}` | Log (exception) | `backend/open_webui/routers/groups.py:168`, `:255` | Adding members failed; also printed when listing members fails | n/a | As above |
| `Error updating group {id}: {e}` | Log (exception) | `backend/open_webui/routers/groups.py:211` | Group save failed | n/a | As above |
| `Error removing users from group {id}: {e}` | Log (exception) | `backend/open_webui/routers/groups.py:292` | Member removal failed | n/a | As above |
| `Error deleting group {id}: {e}` | Log (exception) | `backend/open_webui/routers/groups.py:326` | Group deletion failed | n/a | As above |
| `Failed to add user {user_id} to default group {default_group_id}: {e}` | Log (error) | `backend/open_webui/utils/groups.py:24` | Default-group assignment raised an error (a missing group does not log; it is skipped silently) | n/a | Section 5.13 |
| `Add user error: {err}` | Log (error) | `backend/open_webui/routers/auths.py:1162` | Unexpected Add User failure | n/a | As above |
| `Cannot revoke tokens for user {user_id}: Redis is not configured, existing sessions stay valid until expiry.` | Log (warning) | `backend/open_webui/utils/auth.py:354-357` | An admin set a new password and Redis is not configured | n/a | Explains why the person stays signed in elsewhere (section 5.3) |
| `Model access denied: user_id={user_id} model_id={model_id} reason=model_read_denied` | Log (warning) | chat path `backend/open_webui/utils/models.py:510-514`; `backend/open_webui/utils/access_control/__init__.py:400-404` | A non-admin was refused a model (in chat, also an admin while `BYPASS_ADMIN_ACCESS_CONTROL` is off) | n/a | The same pattern ends in `reason=base_model_unregistered` (`:332-337`), `reason=base_model_read_denied` (`:350-355`) (these two carry `base_model_id={base_model_id}` before the reason and are written for chat refusals too) or, without a model id, `reason=model_unregistered` (`:412`); the chat path also logs `reason=arena_read_denied` and `reason=model_unregistered` with a model id (`backend/open_webui/utils/models.py:475-491`) |

### 10.2 Admin Pages: Users

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `ⓘ Click on the user role button to change a user's role.` | Notice | `src/lib/components/admin/Users/UserList.svelte:470-472` | Always under the Users table | n/a | n/a |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Confirmation | `src/lib/components/common/ConfirmDialog.svelte:143`, `:153`; used at `src/lib/components/admin/Users/UserList.svelte:136-141` | Pressing **Delete User** | Confirm only if the deletion is intended (section 5.4) | n/a |
| `License Error` / `Exceeded the number of seats in your license. Please contact support to increase the number of seats.` | Error banner | `src/lib/components/admin/Users/UserList.svelte:163-176` | Only when licence metadata with a seat count is present and the user count exceeds it | Report to the platform maintainer | Whether a licence key is configured is TO BE CONFIRMED |
| `Running Open WebUI for a team?` | Notice (heading) | `src/lib/components/admin/Users/UserList.svelte:490` | No licence metadata and more than 50 users | n/a | Upstream project message; relevant to the licence question in `../tools/ground-truth.md` |
| `You have more than 50 users, which often means this workspace is supporting organizational use. Open WebUI is free to use as-is, with no restrictions or hidden limits, and we want to keep it that way.` | Notice | `src/lib/components/admin/Users/UserList.svelte:497-499` | As above | n/a | As above |
| `By supporting the project through sponsorship or an enterprise license, you help us stay independent, ship new features faster, improve stability, and grow Open WebUI for the long haul.` | Notice | `src/lib/components/admin/Users/UserList.svelte:505-507` | As above | n/a | As above |
| `Enterprise licenses also include dedicated support, customization options, and more, at a fraction of the cost of building and maintaining this stack internally.` | Notice | `src/lib/components/admin/Users/UserList.svelte:510-512` | As above | n/a | As above |
| `Row {idx + 1}: invalid format.` | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:88` | A CSV line (numbered from 1, header included) lacks exactly four values or a valid role; also a blank last line | Fix or ignore that line | Section 5.6 |
| `Row {idx + 1}: {error}` | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:108` | The server refused that CSV line; `{error}` is the server text from 10.1 | Fix that line | Read the server text |
| `Successfully imported {userCount} users.` | Success | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:121-123` | End of a CSV import (can read 0) | Check the count against the file | Compare with the number of data lines |
| `File not found.` | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:135-136` | **Save** on CSV Import with no file chosen | Choose a file | n/a |
| `ⓘ Ensure your CSV file includes 4 columns in this order: Name, Email, Password, Role.` | Notice | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:285-288` | CSV Import tab | Follow the format | n/a |
| `Click here to select a csv file.` / `{COUNT} document(s) selected.` | Notice | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:277-281` | CSV Import file button before and after choosing | n/a | n/a |
| `{user}'s Chats` | Title | `src/lib/components/admin/Users/UserList/UserChatsModal.svelte:112-114` | Opening a user's chats | n/a | n/a |
| `No chats found for this user.` | Empty state | `src/lib/components/admin/Users/UserList/UserChatsModal.svelte:115` | The person has no chats (or the search matched none) | n/a | Deleted chats are not recoverable from the interface |

### 10.3 Admin Pages: Groups and Permissions

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Group created successfully` | Success | `src/lib/components/admin/Users/Groups.svelte:78` | New group saved | Reopen it to add members | n/a |
| `Default permissions updated successfully` | Success | `src/lib/components/admin/Users/Groups.svelte:95` | Default permissions saved | Remember groups keep their own copies | Section 3.5 |
| `No groups found` / `Use groups to organize your users and assign permissions.` | Empty state | `src/lib/components/admin/Users/Groups.svelte:196-204` | No group, or none matches the search | n/a | n/a |
| `applies to all users with the "user" role` | Notice | `src/lib/components/admin/Users/Groups.svelte:223-225` | Under **Default permissions** | n/a | n/a |
| `Group updated successfully` | Success | `src/lib/components/admin/Users/Groups/GroupItem.svelte:36` | Group saved | n/a | n/a |
| `Group deleted successfully` | Success | `src/lib/components/admin/Users/Groups/GroupItem.svelte:48` | Group deleted | Check the Default Group setting if that group was it | Section 5.13 |
| `{COUNT} members` | Notice | `src/lib/components/admin/Users/Groups/GroupItem.svelte:91` | Each group row | n/a | n/a |
| `No description` | Notice | `src/lib/components/admin/Users/Groups/GroupItem.svelte:100` | Group without a description | n/a | n/a |
| `Custom permissions` / `Uses defaults` | Notice | `src/lib/components/admin/Users/Groups/GroupItem.svelte:107-111` | Whether the group stores any permission values | n/a | Section 3.5 |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Confirmation | `src/lib/components/common/ConfirmDialog.svelte:143`, `:153`; used at `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:116-122` | Pressing **Delete** on a group | Confirm only if intended | n/a |
| `Reset to Defaults` / `Are you sure you want to reset all permissions to their default values? You will still need to save to apply the changes.` | Confirmation | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:124-133` | Pressing **Reset to Defaults** | Confirm, then **Save** | n/a |
| `Permissions reset to defaults` | Success | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:79` | Reset applied to the form (not yet saved) | Press **Save** | n/a |
| `Reset group permissions to match the current default user permissions` | Tooltip | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:295-298` | Hovering **Reset to Defaults** in a group | n/a | n/a |
| `Reset all permissions to their initial configuration values` | Tooltip | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:299` | Hovering **Reset to Defaults** in Default permissions | n/a | n/a |
| `This is a default user permission and will remain enabled.` | Notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:78` and under every other switch (57 occurrences) | A group switch is off but Default permissions turn it on | Change Default permissions instead | Section 3.5 |
| `Warning: Enabling this will allow users to upload arbitrary code on the server.` | Warning (tooltip) | `src/lib/components/admin/Users/Groups/Permissions.svelte:145-147`, `:190-192` | Hovering **Tools Access** or **Skills Access** | Admin decision | n/a |
| `Warning: Enabling this will allow users to run scheduled prompts automatically.` | Warning (tooltip) | `src/lib/components/admin/Users/Groups/Permissions.svelte:1118-1120` | Hovering **Automations** | Admin decision | n/a |
| `Row {idx + 1}: User not found.` | Error | `src/lib/components/admin/Users/Groups/Users.svelte:181` | Group CSV line whose email matches no account | Create the account first or fix the email | Search Users › Overview |
| `Row {idx + 1}: {error}` | Error | `src/lib/components/admin/Users/Groups/Users.svelte:185` | The account look-up for a group CSV line failed | Retry | Server text |
| `Row {idx + 1}: Invalid format.` | Error | `src/lib/components/admin/Users/Groups/Users.svelte:224` | Group CSV line without exactly two values or without an email | Fix that line | Section 5.10 |
| `Successfully imported {userCount} users.` | Success | `src/lib/components/admin/Users/Groups/Users.svelte:233-237` | Group CSV import added at least one member (counts new members) | n/a | n/a |
| `CSV: Name,Email` | Notice | `src/lib/components/admin/Users/Groups/Users.svelte:349` | Group Import menu | n/a | n/a |
| `Importing...` | Status | `src/lib/components/admin/Users/Groups/Users.svelte:317-319` | A group CSV import is running | Wait | n/a |
| `No users were found.` | Empty state | `src/lib/components/admin/Users/Groups/Users.svelte:506-509` | The member search matched no account | Check the spelling | n/a |
| `No models accessible` / `No knowledge bases accessible` / `No tools accessible` | Empty state | `src/lib/components/admin/UserPreviewModal.svelte:84`, `:116`, `:148`; `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte:46`, `:79`, `:112` | The previewed user or group reaches none of that type | n/a | Section 5.8 |
| `{count} of {total} accessible` | Notice | `src/lib/components/admin/UserPreviewModal.svelte:97`, `:129`, `:161`; `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte:59`, `:92`, `:125` | Some but not all items of that type are reachable | n/a | Section 5.8 |
| `{error}` (server text in red) | Error | `src/lib/components/admin/UserPreviewModal.svelte:59-60`; `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte:36-37` | The preview request failed (for example the user or group was deleted) | Reload | 10.1 |

### 10.4 Share Panels and Related Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to make this public` | Tooltip | `src/lib/components/workspace/common/AccessControl.svelte:518-521` | Hovering the visibility menu of a private item without public-sharing permission | Ask an admin about the permission | Section 7.5, Sharing |
| `Only select users and groups with permission can access` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:543` | Visibility **Private** | n/a | n/a |
| `Accessible to all users` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:545` | Visibility **Public** | n/a | n/a |
| `Anyone with the link can view` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:547` | Visibility **Open** | n/a | Kept only for shared chats (section 5.17) |
| `No access grants. Private to you.` | Empty state | `src/lib/components/workspace/common/AccessControl.svelte:698-702` | Private item with an empty Access List | n/a | n/a |
| `No users were found.` | Empty state | `src/lib/components/workspace/common/MemberSelector.svelte:317-320` | The Add Access search matched no person or group | Type more of the name or email | Section 5.16 |
| `Only invited users can access` / `Visible to all users` | Notice | `src/lib/components/workspace/common/Visibility.svelte:46-50` | Group channel visibility menu | n/a | `channels-and-direct-messages.md` |
| `Saved` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:307`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:219`; `src/lib/components/workspace/Skills/SkillEditor.svelte:105`; `src/lib/components/notes/NoteEditor.svelte:1005`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1232` | An access change was saved | Reopen the dialog to see what was kept | Section 5.17 |
| `Access updated` | Success | `src/lib/components/chat/ShareChatModal.svelte:81` | A shared chat's access change was saved | As above | As above |
| `You do not have permission to upload files.` | Error | `src/lib/components/chat/MessageInput.svelte:918-921` | `chat.file_upload` is off for the person | Ask an admin | Effective permission (section 3.5) |
| `You do not have permission to upload web content.` | Error | `src/lib/components/chat/Chat.svelte:1790-1793` | `chat.web_upload` is off | Ask an admin | As above |
| `Access prohibited` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:224-226`; `src/lib/components/chat/Chat.svelte:3051-3052` | Cloning a chat without `chat.import` | Ask an admin | As above |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes roles, groups, permissions, shares or settings. "Ask an admin
to confirm" below means asking someone with the `admin` role to look, without changing anything,
and to make any change through the normal admin process. Support contacts and escalation routes are
TO BE CONFIRMED (`../tools/ground-truth.md`, Contacts). Never request or forward passwords or user
import CSV files.

### 11.1 "I signed up but it just says my account is pending"

**Symptom.** After signing in, the person sees `Account Activation Pending` /
`Contact Admin for WebUI Access` and `Your account status is currently pending activation.`, unless
an admin replaced that text (`src/lib/components/layout/Overlay/AccountPending.svelte:31-51`).

**Likely causes, in order.**
1. New accounts are created with the Default User Role, code default `pending`, and no admin has
   approved this one yet (`backend/open_webui/config.py:1720`, `:3096`).
2. An admin previously set the account back to `pending` (suspension).
3. A role value other than `user` or `admin` (the interface treats it as pending,
   `src/routes/(app)/+layout.svelte:445-446`).

**Diagnostic steps.** Ask for a screenshot of the screen and the email the person signed up with.
Ask an admin to confirm, in Users › Overview, the Role shown for that email.

**Resolution.** Explain that access needs an admin's approval and that nothing is emailed when it
happens; after approval the person presses **Check Again** or reloads. Who approves accounts, and
on what criteria, is TO BE CONFIRMED.

**Escalation.** Send the email address used, the date of sign-up and the screenshot to the admin
team (TO BE CONFIRMED).

### 11.2 "My account was approved but I still see the pending screen"

**Symptom.** The person was told they are approved but still sees the waiting screen.

**Likely causes, in order.**
1. The page has not been reloaded: nothing pushes the new role to an open screen
   (`src/lib/components/layout/Overlay/AccountPending.svelte:59-67`).
2. The admin changed a different account (similar names or emails).
3. The role was set to something other than `user` or `admin`.
4. With SSO role management on, the identity provider's mapping set the role again at sign-in
   (`sso-oauth-oidc-and-scim.md`).

**Diagnostic steps.** Ask the person to press **Check Again**, or reload. Ask an admin to confirm
the Role column for the exact email.

**Resolution.** Usually a reload. If the role is still `pending`, escalate to an admin.

**Escalation.** Email address, time of the reported approval, whether the person signs in with SSO.

### 11.3 "The admin page says 'The requested action has been restricted as a security measure.'"

**Symptom.** An admin saving or deleting a user gets that pop-up.

**Likely causes, in order.**
1. The target is the primary admin (earliest-created account) and the admin is someone else
   (`backend/open_webui/routers/users.py:923-933`).
2. The primary admin tried to change their own role (`:935-940`).
3. Someone tried to delete the primary admin or their own account (`:1046-1053`, `:1080-1084`).
4. On a status screen: **User Status** is turned off (`:575-579`).

**Diagnostic steps.** Ask which account was being changed and by whom. In Users › Overview the table
starts sorted by creation date, oldest first, so the primary admin is normally the first row
(`src/lib/components/admin/Users/UserList.svelte:47-48`).

**Resolution.** Explain the rule in section 3.3. Changes to the primary admin can be made only by the
primary admin; deletion of it is not possible in the application.

**Escalation.** If a change to the primary admin is genuinely needed, escalate to the platform
maintainer with the request and the reason.

### 11.4 "There's no delete button for this user"

**Symptom.** An admin sees no trash icon on a row.

**Likely causes, in order.** The row's role is `admin`; the interface hides Delete for every admin
row (`src/lib/components/admin/Users/UserList.svelte:448-461`).

**Diagnostic steps.** Confirm the role shown on that row.

**Resolution.** Explain that an admin account must first be changed to `user` or `pending` by an
admin before it can be deleted, and that the primary admin cannot be deleted (section 3.3).
Deletion is permanent (section 5.4), so confirm the request through the proper approval route
(TO BE CONFIRMED).

**Escalation.** Account email, the reason for removal, and who approved it.

### 11.5 "My user import CSV keeps saying 'invalid format'"

**Symptom.** Pop-ups such as `Row 5: invalid format.` (pattern `Row {idx + 1}: invalid format.`)
during Add User › CSV Import, or `Row 3: Invalid format.` during a group member import.

**Likely causes, in order.**
1. A blank last line in the user import (a file ending with a line break): the message names the
   line after the last account and is harmless (`src/lib/components/admin/Users/UserList/AddUserModal.svelte:73-91`).
2. A comma inside a name or password, which splits the line into too many values.
3. A role other than `admin`, `user` or `pending`.
4. The wrong column count: four for user import, two for group import.
5. Using the Admin Settings › Database user export (`id,name,email,role`) as an import file.

**Diagnostic steps.** Ask which row numbers were reported; row 1 is the header line. Ask the admin
to check those lines in the file themselves; do not request the file (it holds passwords).

**Resolution.** Explain the format in sections 5.6 and 5.10. Lines that import successfully are not
affected by bad lines.

**Escalation.** Only if valid-looking lines fail: the row numbers, the pop-up texts and the time.

### 11.6 "I turned a permission off but people still have it"

**Symptom.** After switching something off in Default permissions or in a group, users still see the
feature.

**Likely causes, in order.**
1. Another group the user belongs to still grants it; permissions only add (section 3.5).
2. A group created earlier from the defaults (or reset to defaults) still holds its own `on` value.
3. It was switched off in a group while Default permissions still grant it; the editor shows `This
   is a default user permission and will remain enabled.`
4. The user's screen was loaded before the change; menus update after a reload.
5. The person is an admin; admins skip permission checks.

**Diagnostic steps.** Ask for the user's email and the feature name. Ask an admin to open **Edit
User** to list the person's groups, then check each group's Permissions tab and Default permissions
for that switch (section 7.5 gives the switch name).

**Resolution.** Explain the additive rule and the worked example in section 3.6; any change is an
admin task.

**Escalation.** User email, feature, the groups listed, and when the change was made.

### 11.7 "I gave a group a permission but a member still can't see the feature"

**Symptom.** A group switch is on but a member does not get the feature.

**Likely causes, in order.**
1. The global feature switch is off for the whole site (section 7.6), for example Channels,
   Web Search, API keys or User Webhooks, which are off in code.
2. The member's screen has not been reloaded since the change.
3. The person is not actually a member (for example SSO sync removed them at sign-in).
4. A parent switch is off. Several dependent switches only take effect together with their parent:
   **Allow Chat System Prompt** and **Allow Chat Params** need **Allow Chat Controls**
   (`src/lib/utils/settings-access.ts:3-8`; `backend/open_webui/routers/users.py:500-518`), and
   **Enforce Temporary Chat** is undone when **Allow Temporary Chat** is off
   (`src/lib/components/chat/Chat.svelte:2024-2043`).
5. The person's role is `pending`.

**Diagnostic steps.** Ask the person to reload. Ask an admin to confirm membership in the group's
Users tab and the global switch for the feature.

**Resolution.** Guidance only; global switches and memberships are admin changes.

**Escalation.** User email, group name, feature, time of the change.

### 11.8 "I shared it with my colleague but they can't see it"

**Symptom.** An owner shared a model, knowledge base, prompt, tool, skill, note or folder, but the
recipient does not see it or cannot use it.

**Likely causes, in order.** Work through section 5.17: the entry was removed on save (no
permission for people, groups or public); the recipient lacks the Workspace section for that item
type; the recipient left or was removed from the group; the recipient is pending; a custom model's
base model is not readable by them; the recipient's screen needs a reload.

**Diagnostic steps.** Ask the owner to reopen the item's **Access** dialog and say what the Access
List and visibility show now (a removed entry is gone after reopening). Ask the recipient to reload
and to say where they are looking (Workspace, chat model list, `#` in chat).

**Resolution.** Explain what the dialog now shows and which permission is missing (section 7.5).
Permission changes are admin tasks.

**Escalation.** Item type and name, owner email, recipient email, group name if any, what the
reopened dialog shows, and the time of sharing.

### 11.9 "I can't find the person or group I want to share with"

**Symptom.** The Add Access dialog does not list someone.

**Likely causes, in order.**
1. Only the first 30 matches are listed; the person needs a more specific search
   (`src/lib/components/workspace/common/MemberSelector.svelte:61-77`).
2. The group's **Who can share to this group** setting is **No one**, or **Members** and the sharer is
   not a member (section 5.12).
3. Sharing with people or groups is not allowed for the sharer (`access_grants.allow_users`,
   `access_grants.allow_groups`), so that part of the dialog is hidden.
4. The person or group is already on the Access List (already-added entries are hidden), or it is
   the sharer's own account.
5. The account does not exist yet.

**Diagnostic steps.** Ask the sharer to type the full email address in the search. Ask an admin to
confirm the group's share setting.

**Resolution.** Guidance; share settings and permissions are admin changes.

**Escalation.** Sharer email, the person or group sought, the item.

### 11.10 "Someone shared a model with me but it says 'Model not found'"

**Symptom.** The model appears in the list but sending a message fails with `Model not found`.

**Likely causes, in order.**
1. The custom model is built on a base model the person cannot read
   (`backend/open_webui/utils/access_control/__init__.py:304-358`, `:405-409`; in chat
   `backend/open_webui/utils/models.py:517-521`).
2. The grant was removed or the person left the group since the list loaded.
3. The base model has no registered model record, which makes it admin-only
   (`backend/open_webui/utils/access_control/__init__.py:330-338`).
4. Availability rather than access: the model, or the custom model's base model, is not currently
   offered by any connection (for example it was removed or renamed, or the connection is down) and
   no fallback applies. This refuses everyone, admins included; a custom model stays in the list
   without its base model (section 3.7, steps 1 and 3; `backend/open_webui/utils/models.py:210-238`).

**Diagnostic steps.** Ask for the model name and the time. Ask whether colleagues get the same
message with the same model; if everyone does, admins included, cause 4 is likely. Ask an admin to
use **Preview Access** for the person: the preview does not check the base-model chain, so a model
listed there can still fail (section 5.8).

**Resolution.** Escalate to an admin or the model owner; details in
`workspace-models-and-model-access.md`.

**Escalation.** Model name, user email, time, screenshot. The server log has a `Model access denied`
line with the reason (section 10.1). An availability refusal (cause 4) has no such line, only
`Error processing chat metadata: Model not found` (`backend/open_webui/main.py:1641`).

### 11.11 "The Workspace link has disappeared" or "I don't have a Workspace"

**Symptom.** No Workspace entry in the sidebar or user menu; opening a `/workspace/...` address goes
back to the home page.

**Likely causes, in order.**
1. None of the five Workspace Access permissions is on for the person; all are off in code
   (section 7.5; `src/lib/components/layout/Sidebar.svelte:164-172`).
2. They have access to some sections but not the one they opened, which redirects home
   (`src/routes/(app)/workspace/+layout.svelte:80-101`).
3. Tools needs plugins enabled as well.

**Diagnostic steps.** Ask which section they need and whether others in their team see it.

**Resolution.** Explain that Workspace access is granted by admins through Default permissions or a
group.

**Escalation.** User email, the section needed, the business reason.

### 11.12 "My group membership keeps disappearing"

**Symptom.** An admin adds someone to a group, but the membership is gone after the person signs in
again.

**Likely causes, in order.**
1. SSO, LDAP or trusted-header group management replaces memberships at each sign-in to match the
   identity provider (`backend/open_webui/models/groups.py:516-572`;
   `backend/open_webui/utils/oauth.py:1730-1763`).
2. Two groups share the same name, and sync matched the other one.

**Diagnostic steps.** Ask how the person signs in (SSO or password). Ask an admin to compare the
group name with the name the identity provider sends (TO BE CONFIRMED per provider).

**Resolution.** Explain that group membership for SSO users is managed in the identity provider when
group management is on.

**Escalation.** User email, group name, sign-in method, time of the last sign-in; route to the team
that manages the identity provider groups (TO BE CONFIRMED).

### 11.13 "New users aren't being added to the default group"

**Symptom.** Recently created accounts are not members of the Default Group.

**Likely causes, in order.**
1. The Default Group was deleted or never set; a missing group is skipped silently
   (`backend/open_webui/utils/groups.py:20-24`; `backend/open_webui/models/groups.py:582-585`).
2. SSO group sync removed it right after account creation (section 5.15).
3. The accounts were created by SCIM, which does not apply the Default Group.
4. The accounts existed before the Default Group was set; it applies only at creation.

**Diagnostic steps.** Ask an admin to check Admin Settings › Authentication › Default Group and the
group's Users tab; ask how the accounts were created.

**Resolution.** Guidance and escalation.

**Escalation.** Example account emails, creation dates and method, the Default Group name.

### 11.14 "Other people can see my name and email"

**Symptom.** A person notices their name and email in someone else's share picker or mention list.

**Likely causes, in order.** By design, any signed-in `user` or `admin` can search all accounts by
name or email and see name, email, role and bio (`backend/open_webui/routers/users.py:137-161`;
section 6.5). Person look-ups also show group names
(`backend/open_webui/routers/users.py:814-832`).

**Diagnostic steps.** None needed beyond confirming where they saw it.

**Resolution.** Explain that this directory behaviour is how sharing works in this version. Whether
it is acceptable for this deployment is a privacy question, TO BE CONFIRMED.

**Escalation.** Route privacy concerns to the U of T Privacy Office (privacy.utoronto.ca) and the
platform maintainer; do not forward other people's details.

### 11.15 "Can an admin read my chats?"

**Symptom.** A user asks whether administrators can see their conversations.

**Likely causes, in order.** With `ENABLE_ADMIN_CHAT_ACCESS` on (the code default), admins can list
and open any non-admin user's chats from Admin Panel › Users (section 5.7). The live value is TO BE
CONFIRMED.

**Diagnostic steps.** None.

**Resolution.** State the code behaviour and that the production setting and the policy on its use
are TO BE CONFIRMED.

**Escalation.** Policy questions go to the service owner and the Privacy Office (privacy.utoronto.ca).

### 11.16 "We deleted a user by mistake. Can we get their chats back?"

**Symptom.** An account was deleted and its chats are wanted back, or someone asks what happened to
a departed person's content.

**Likely causes, in order.** Deletion removes the account, its chats (with messages and share
snapshots) and group memberships permanently; owned files, knowledge bases, models, prompts, tools,
notes and other content stay behind under the deleted id (section 5.4).

**Diagnostic steps.** Ask for the email of the deleted account and the approximate deletion time.

**Resolution.** The application has no undo. Recovery of chats would need a database restore; backup
availability is TO BE CONFIRMED. Content left behind is still visible to admins with admin bypass on.

**Escalation.** Email of the deleted account, deletion time, who deleted it, what is needed back.

### 11.17 "I reset a user's password but they are still signed in on another device"

**Symptom.** After an admin set a new password in Edit User, an existing session keeps working.

**Likely causes, in order.** Ending existing sign-ins needs Redis; without it the server logs a
warning and existing sessions stay valid until they expire (section 5.3;
`backend/open_webui/utils/auth.py:349-371`).

**Diagnostic steps.** None for tier 1.

**Resolution.** Escalate. Whether Redis is configured in production is TO BE CONFIRMED. If the
reset was prompted by a suspected compromise, stop and refer it as a security incident
(security.utoronto.ca).

**Escalation.** User email, time of the reset, the reason for the reset.

### 11.18 "The green 'active' dot or the active-user count looks wrong"

**Symptom.** Someone shows as active after leaving, or the count seems off.

**Likely causes, in order.**
1. "Active" means activity in the last 3 minutes, and activity is recorded at most once a minute per
   user per server worker; an open browser tab keeps sending heartbeats (section 7.4).
2. The Add Access people list does not show a live dot: search results do not carry activity data
   (section 6.5).
3. Non-admins see the count only when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is on.

**Diagnostic steps.** Ask where the indicator was seen (Users table, user menu, share dialog).

**Resolution.** Explain the 3-minute window.

**Escalation.** Not normally needed.

### 11.19 "I set it to Public and it said 'Saved', but it's private again"

**Symptom.** The owner chose **Public**, saw `Saved`, but on reopening the dialog the item is
Private, or a person or group they added is missing.

**Likely causes, in order.** The server removed entries the owner may not make (section 5.17, items
1 to 3); the open dialog kept showing the choice until it was reopened (section 5.16, step 7).

**Diagnostic steps.** Ask the owner which entries vanished and what kind of item it is.

**Resolution.** Explain which permission is needed (section 7.5, Sharing and Access grants) and that
granting it is an admin decision.

**Escalation.** Owner email, item type and name, the entries that vanished.

## 12. Local Customisations

Checked with read-only `git diff main...uoft` (fork commits) and `git diff` (uncommitted working
tree) over every file in section 13, plus `src/lib/constants/permissions.ts`, the user import
template files and the pending screen.

- **Fork commits.** One change touches this area: commit `aeed1832c` adds `showInlineCitations` and
  `hideProcessingDetails` to the `InterfaceSettings` model
  (`backend/open_webui/models/users.py:99-100`). Because the server discards every
  `InterfaceSettings` field from a non-admin's settings save when that person lacks
  `settings.interface` (`backend/open_webui/routers/users.py:493-498`), the fork's **Hide Processing
  Details** and **Inline Citations** choices are governed by the **Interface Settings Access**
  permission like the other Interface settings. With the permission off, those two settings cannot
  be saved by users; what they see then is described in `user-settings-and-personalisation.md`.
- **Uncommitted working tree.** No file in this area's scope has uncommitted changes. The one
  uncommitted change in `src/lib/i18n/locales/en-US/translation.json` rewords the Hide Processing
  Details description and does not affect any text quoted here.
- Everything else in this document matches upstream Open WebUI v0.11.4: roles, groups, permission
  keys and defaults, sharing and the admin pages are unchanged by the fork.

## 13. Source File Index

### 13.1 Files in Scope

| File | What it does in this area |
|---|---|
| `backend/open_webui/routers/users.py` | Users API: list, search, permissions, default permissions, own settings, status, info, usage, per-user lookups, admin edit and delete, user preview |
| `backend/open_webui/routers/groups.py` | Groups API: list (role-dependent), create, info, export, update, add and remove members, delete, group preview |
| `backend/open_webui/models/users.py` | `user` table, `InterfaceSettings` (fork fields at `:99-100`), API response shapes, search and sort query, primary-admin lookup, activity writes and checks, deletion order |
| `backend/open_webui/models/groups.py` | `group` and `group_member` tables, share-setting filter, membership changes, name-based sync |
| `backend/open_webui/models/access_grants.py` | `access_grant` table, grant normalization and legacy conversion, access checks, batch checks, "users with access" |
| `backend/open_webui/utils/access_control/__init__.py` | `get_permissions`, `has_permission`, config-stored grant checks, connection access, `filter_allowed_access_grants`, model access checks |
| `backend/open_webui/utils/access_control/files.py` | File access through knowledge bases, channels, shared chats and models; folder file filtering |
| `backend/open_webui/utils/access_control/folders.py` | Folder access with inheritance from parent folders |
| `backend/open_webui/utils/groups.py` | Default-group assignment for new accounts |
| `backend/open_webui/config.py` | `DEFAULT_USER_ROLE`, `DEFAULT_GROUP_ID`, every `USER_PERMISSIONS_*` variable, `DEFAULT_USER_PERMISSIONS`, `BYPASS_ADMIN_ACCESS_CONTROL`, the `DEFAULT_CONFIG` entries for these keys |
| `src/routes/(app)/admin/users/+page.svelte`, `src/routes/(app)/admin/users/[tab]/+page.svelte` | `/admin/users` redirect and the tab route |
| `src/lib/components/admin/Users.svelte` | Overview and Groups tabs with counts |
| `src/lib/components/admin/Users/UserList.svelte` | Users table, search, sort, active dot, row actions, notices |
| `src/lib/components/admin/Users/UserList/AddUserModal.svelte` | Add User form and CSV import parser |
| `src/lib/components/admin/Users/UserList/EditUserModal.svelte` | Edit User dialog (role, name, email, OAuth ID, password, groups) |
| `src/lib/components/admin/Users/UserList/UserChatsModal.svelte` | A user's chat list for admins |
| `src/lib/components/admin/UserPreviewModal.svelte` | User Preview dialog |
| `src/lib/components/admin/Users/Groups.svelte` | Groups list, New Group, Default permissions entry |
| `src/lib/components/admin/Users/Groups/GroupItem.svelte` | One group row; save and delete handlers; `?id=` deep link |
| `src/lib/components/admin/Users/Groups/EditGroupModal.svelte` | Group and Default permissions dialog; Reset to Defaults |
| `src/lib/components/admin/Users/Groups/General.svelte` | Group name, description, share setting, delete |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | Every permission switch and the "default user permission" notice |
| `src/lib/components/admin/Users/Groups/Users.svelte` | Group membership table and member CSV import |
| `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte` | Group Preview tab |
| `src/lib/apis/users/index.ts` | Front-end calls for the users API. `updateUserRole` (`:115-144`) targets `/users/update/role`, which no backend route serves, and `getUserGroups` (`:4-29`); neither has a caller in `src/` |
| `src/lib/apis/groups/index.ts` | Front-end calls for the groups API (no calls for group export or member listing) |
| `src/lib/components/workspace/common/AccessControl.svelte` | The share panel: visibility, public write, Access List, Read and Write |
| `src/lib/components/workspace/common/AccessControlModal.svelte` | The **Access Control** dialog wrapper |
| `src/lib/components/workspace/common/AddAccessModal.svelte` | The **Add Access** dialog |
| `src/lib/components/workspace/common/MemberSelector.svelte` | People and group picker (first 30 search results) |
| `src/lib/components/workspace/common/Visibility.svelte` | Public or Private menu used by group channels |
| `src/lib/components/workspace/common/ViewSelector.svelte` | "All", "Created by you", "Shared with you" list filter (`:15-19`) used on workspace and admin lists |
| `src/lib/components/workspace/common/ValvesModal.svelte`, `TagSelector.svelte`, `ManifestModal.svelte`, `PluginTranslations.svelte`, `CommunityDiscover.svelte` | Opened; not access-related (valves, tag filter, plugin support links, valve translations, community link); covered by the tools and functions documents |
| `src/lib/components/common/AccessButton.svelte` | The **Access** button that opens share dialogs |
| `src/lib/utils/settings-access.ts` | Permission rules for personal settings (system prompt, parameters, chat import, export and delete, API keys, notification targets, temporary chats) |

### 13.2 Files Consulted Outside Scope

| File | Why |
|---|---|
| `backend/open_webui/routers/auths.py` | Add User endpoint, default role and group at creation, permissions in the session, admin contact for pending users |
| `backend/open_webui/models/auths.py` | Account creation and the `auth` row deletion |
| `backend/open_webui/utils/auth.py` | Role checks, password rules, token revocation, activity writes |
| `backend/open_webui/models/chats.py` | Chat deletion when a user is deleted |
| `backend/open_webui/routers/chats.py` | Admin chat access, chat permissions, shared chat grants |
| `backend/open_webui/events.py`, `backend/open_webui/socket/main.py` | Event names, webhooks, socket disconnect, heartbeat |
| `backend/open_webui/env.py`, `backend/open_webui/constants.py` | Environment switches and message text |
| `backend/open_webui/internal/db.py`, `backend/open_webui/models/config.py` | SQLite pragmas, sessions, config reads and seeding |
| `backend/open_webui/utils/models.py`, `backend/open_webui/main.py` | Model list filtering, chat-path model access, feature flags, `/api/usage` |
| `backend/open_webui/utils/oauth.py` | SSO role, default group and group sync |
| `backend/open_webui/utils/misc.py`, `backend/open_webui/utils/tools.py` | Activity throttle; built-in tool permission checks |
| `backend/open_webui/migrations/versions/37f288994c47_add_group_member_table.py` | `group_member` constraints |
| `src/lib/constants/permissions.ts` | Interface fallbacks for unset permission keys |
| `src/lib/components/common/ConfirmDialog.svelte`, `src/lib/components/layout/Overlay/AccountPending.svelte` | Default confirmation text; the pending screen |
| `src/routes/+layout.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/(app)/admin/+layout.svelte`, `src/routes/(app)/admin/+page.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Session load, pending gate, admin guard, admin redirects |
| `src/lib/components/admin/Settings/Authentication.svelte`, `General.svelte`, `Database.svelte` | Default role and group, User Status, user export |
| Share dialog callers: `ModelEditor.svelte`, `KnowledgeBase.svelte`, `CreateKnowledgeBase.svelte`, `PromptEditor.svelte`, `ToolkitEditor.svelte`, `SkillEditor.svelte`, `NoteEditor.svelte`, `FolderShareModal.svelte`, `ShareChatModal.svelte`, `ChannelModal.svelte` | Which permissions shape each share dialog and how changes are saved |
| Permission check sites listed in section 7.5 | What each permission controls |
| `static/static/user-import.csv`, `backend/open_webui/static/user-import.csv` | The user import template |
| `backend/open_webui/routers/openai.py`, `backend/open_webui/routers/ollama.py` | Provider-router model access checks, their model-list filters, and where `BYPASS_MODEL_ACCESS_CONTROL` applies or does not (section 3.7) |
| `backend/open_webui/utils/chat.py`, `backend/open_webui/utils/actions.py`, `backend/open_webui/functions.py` | The model check just before a chat is sent, the message-action check and the pipe-model check (sections 3.7, 10.1) |
| `backend/open_webui/utils/middleware.py` | Arena model pick (section 3.7); code-interpreter permission check (section 7.5) |
| `backend/open_webui/routers/models.py`, `backend/open_webui/routers/knowledge.py`, `backend/open_webui/routers/prompts.py`, `backend/open_webui/routers/tools.py`, `backend/open_webui/routers/skills.py`, `backend/open_webui/routers/notes.py`, `backend/open_webui/routers/files.py` | Workspace and public-sharing permission checks; admin-bypass sites (sections 3.7, 7.5) |
| `backend/open_webui/routers/folders.py`, `backend/open_webui/routers/channels.py`, `backend/open_webui/routers/calendar.py`, `backend/open_webui/routers/automations.py`, `backend/open_webui/routers/memories.py`, `backend/open_webui/routers/audio.py`, `backend/open_webui/routers/images.py` | Server-side checks for folders, channels (including `sharing.public_channels`), calendars, automations, memories, speech and image generation (section 7.5) |
| `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/ChatControls.svelte`, `src/lib/components/chat/Controls/Controls.svelte`, `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/InputMenu.svelte`, `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/chat/Messages/UserMessage.svelte`, `src/lib/components/chat/ModelSelector.svelte`, `src/lib/components/chat/Navbar.svelte` | Chat-screen permission checks (section 7.5); `Chat.svelte` also shows chat refusals (section 3.7) |
| `src/lib/components/chat/SettingsModal.svelte`, `src/lib/components/chat/Settings/Account.svelte` | Settings tabs and sections gated by permissions (section 7.5) |
| `src/lib/components/layout/Sidebar.svelte`, `src/lib/components/layout/Sidebar/ChatItem.svelte`, `src/lib/components/layout/Sidebar/ChatMenu.svelte`, `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte`, `src/lib/components/layout/Sidebar/UserMenu.svelte`, `src/lib/components/layout/Navbar/Menu.svelte` | Sidebar, chat menu and user menu permission checks; the active-user count (sections 7.4, 7.5) |
| `src/lib/components/layout/ChatsModal.svelte` | Opens a user's chat in the shared-chat viewer (sections 2.1, 5.7) |
| `src/lib/components/workspace/Models.svelte`, `src/lib/components/workspace/Models/Knowledge.svelte`, `src/lib/components/workspace/Models/ModelMenu.svelte`, `src/lib/components/workspace/Prompts.svelte`, `src/lib/components/workspace/Prompts/PromptMenu.svelte`, `src/lib/components/workspace/Skills.svelte`, `src/lib/components/workspace/Skills/SkillMenu.svelte`, `src/lib/components/workspace/Tools.svelte`, `src/lib/components/workspace/Tools/ToolMenu.svelte` | Workspace import, export and knowledge-upload permission checks (section 7.5) |
| `src/routes/(app)/workspace/+layout.svelte`, `src/routes/(app)/notes/+layout.svelte`, `src/routes/(app)/automations/+layout.svelte`, `src/routes/s/[id]/+page.svelte` | Section guards that send people without the permission home; the shared-chat clone check (sections 5.17, 7.5) |
| `src/lib/components/admin/Settings/Models.svelte`, `src/lib/components/admin/Settings/ExternalKnowledge.svelte`, `src/lib/components/AddToolServerModal.svelte`, `src/lib/components/AddTerminalServerModal.svelte` | Share panels on admin-only screens (section 5.16) |
| `src/lib/components/channel/MessageInput/MentionList.svelte` | Channel mention list, filled from the user search (section 6.5) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys quoted in sections 5.15 and 7.2 |

## 14. Open Questions

The code cannot settle the items below. Each heading says who can answer. Every item marked TO BE
CONFIRMED earlier in this document is repeated here, along with the security-sensitive referrals.

### 14.1 Live Data (Answered by an Admin or a Read-Only Database Query)

- The current role of each account, and how many accounts are `pending` now (Users › Overview).
- Which account is the primary admin (earliest `created_at`), and whether that person still works with the service (section 3.3).
- Which other accounts hold the `admin` role.
- Group names, descriptions and members, and each group's **Who can share to this group** setting (sections 5.9 to 5.12).
- Each group's stored permission values, and which groups show **Custom permissions** rather than **Uses defaults** (section 3.5).
- Whether any two groups share a name; identity-provider group sync matches groups by name (section 5.9).
- The live value of `user.permissions` (Default permissions), key by key, compared with the code defaults in section 7.5.
- The live values of `ui.default_user_role` and `ui.default_group_id`, and whether the Default Group still exists (sections 5.13, 5.15).
- The live value of `users.enable_status` (**User Status**, section 7.2).
- Access grants per resource: which models, knowledge bases, prompts, tools, skills, notes, folders, channels and shared chats are Public (`user:*`), Open (`anyone:*`) or shared with named people or groups (section 6.3).
- Whether `access_grant` holds grants that name deleted users or groups and so match no one (sections 5.4, 5.13).
- Which content is still owned by deleted accounts (files, knowledge bases, models, prompts, tools and the rest, section 5.4).
- The live values of the global feature switches in section 7.6 (`notes.enable`, `channels.enable`, `folders.enable`, `calendar.enable`, `automations.enable`, `ui.enable_user_webhooks`, `auth.enable_api_keys`, `web.search.enable`, `image_generation.enable`, `code_interpreter.enable`, `memories.enable`, `direct.integrations.enable`, `ui.enable_message_rating`).
- Whether arena models are on (`evaluation.arena.enable`), which arenas `evaluation.arena.models` holds, and each arena's access list (section 3.7).
- Which offered base models have no model record and are therefore admin-only, and the value of `ui.default_models` that the custom-model fallback uses (section 3.7).
- Whether an admin replaced the pending screen's title and text (`ui.pending_user_overlay_title`, `ui.pending_user_overlay_content`), and whether "show admin details" and an admin contact email are set (section 3.3, section 11.1).
- Which event webhooks are configured (`events.webhooks` or a legacy single webhook URL), where they deliver, and whether event functions are active; these messages carry the acting user's name and email (section 9).
- How each existing account was created (sign-up, Add User or CSV, LDAP, SSO, trusted headers or SCIM), which decides whether the Default Group was applied (section 5.15).

### 14.2 Deployment Environment (Answered by the Platform Maintainer)

- The production host name; URLs in this document are relative to the site root.
- The live value of `ENABLE_ADMIN_CHAT_ACCESS` (code default on): whether admins can list and open users' chats (sections 3.7, 5.7, 11.15).
- The live value of `BYPASS_ADMIN_ACCESS_CONTROL`, or of its fallback `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS` (code default on) (section 3.7).
- The live value of `BYPASS_MODEL_ACCESS_CONTROL` (code default off) (section 3.7).
- The live value of `ENABLE_CUSTOM_MODEL_FALLBACK` (code default off), which decides whether a custom model whose base model is unavailable falls back to a default model (section 3.7, step 3).
- The live values of `DEFAULT_GROUP_SHARE_PERMISSION`, `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL`, `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`, `ENABLE_PROFILE_IMAGE_URL_FORWARDING`, `PROFILE_IMAGE_ALLOWED_MIME_TYPES` and `ENABLE_ADMIN_EXPORT` (sections 7.1 to 7.4).
- The live value of `ENABLE_PLUGINS`, which decides whether **Tools Access** is offered in the permission editor (section 5.11).
- Whether `ENABLE_PERSISTENT_CONFIG` or `RESET_CONFIG_ON_START` change where the settings in section 6.4 come from (`../tools/ground-truth.md`, Settings).
- The database engine (SQLite or PostgreSQL): on SQLite the code does not switch on foreign-key enforcement, so membership rows of deleted groups and chat-to-file links of deleted users can remain (sections 5.4, 5.13).
- The live value of `DATABASE_ENABLE_SESSION_SHARING` (code default off), which decides whether a failed user deletion can leave its earlier steps done (section 5.4).
- Whether Redis is configured in production: without it, a new password set by an admin does not end the person's other sessions (sections 5.3, 11.17).
- The number of server worker processes, since the activity throttle applies per worker (section 7.4).
- Whether SSO, LDAP or trusted-header group management is on, which replaces hand-made memberships at each sign-in (section 4, Group sync; section 11.12).
- Whether SSO role management is on, which can overwrite a role set in Edit User at the next SSO sign-in (sections 5.2, 11.2).
- The group names each identity provider sends in its group claim, per provider (section 11.12).
- Whether SCIM provisioning is in use; SCIM-created accounts do not get the Default Group (section 5.15).
- Whether a licence key is configured (the **License Error** banner needs licence metadata with a seat count, section 10.2).
- Whether database backups exist, how often they run and how long they are kept: they are the only route the code leaves for recovering a deleted user's chats (sections 5.4, 11.16).
- Security-sensitive: whether any credential-related records remain after a user is deleted. Refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- Security-sensitive: how sharing restrictions and model access control are enforced on server paths beyond those described in sections 3.7 and 5.17. Refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

### 14.3 People and Process (Answered by the Service Owner)

- Who approves pending accounts, on what criteria, and how approval requests reach them (sections 5.1, 11.1).
- The admin team that tier 1 escalates account, group and permission requests to, and the route for reaching it (section 11).
- Support contacts, escalation routes and hours for MedIT GPT; none exist in the repository (`../tools/ground-truth.md`, Contacts).
- How people learn that their account was approved, since the application tells them nothing (section 5.1).
- How an admin passes on the email address and initial password of an account created with Add User or CSV import (section 5.5).
- Who may request permission changes (for example Workspace access or public sharing), who approves them, and what business reason is needed (sections 11.6, 11.11).
- The approval route for deleting a user (sections 5.4, 11.4).
- What should happen to content a deleted or departed person leaves behind, since no ownership-transfer feature exists (sections 5.4, 11.16).
- The policy on when admins may open users' chats, given that chats can contain personal and health information (sections 5.7, 11.15).
- Whether letting any signed-in user search every account's name, email, role and bio is acceptable for this deployment; a privacy question for the U of T Privacy Office (privacy.utoronto.ca) (sections 6.5, 11.14).
- Which team manages identity-provider groups, and how group changes are requested (section 11.12).
- Who holds the primary admin account, and the procedure if that person leaves, since the application blocks its demotion and deletion (section 3.3).
- Who reviews event webhook destinations, since webhook messages carry personal data (section 9).
- Which `LICENSE` §4 exception the deployment relies on; the "Running Open WebUI for a team?" notice appears above 50 users (section 10.2; `../tools/ground-truth.md`, Licence).

### 14.4 Product Behaviour (Answered by the Platform Maintainer or Upstream Open WebUI)

- Whether approving an account should notify the person; the code sends nothing (section 5.1).
- Whether `sharing.public_channels`, checked when channels are saved but absent from the defaults and the editor, is meant to remove public channel grants for every non-admin (section 7.5).
- Whether SCIM-created accounts are meant to skip the Default Group (section 5.15).
- Whether admins with `BYPASS_ADMIN_ACCESS_CONTROL` off are meant to see base models without a model record that the chat check then refuses (section 3.7).
- Whether message action buttons and the Ollama router's `/ollama/v1/...` endpoints are meant to keep checking model access while `BYPASS_MODEL_ACCESS_CONTROL` is on (section 3.7).
- Whether the group editor is meant to store the interface's built-in values for unset keys when a group that **Uses defaults** is saved (section 3.5).
- Whether duplicate group names should be prevented, given that sync matches groups by name (section 5.9).
- Whether the user search's `groups` and `is_active` fields, which carry their defaults in search results, are meant to be filled (section 6.5).
- Whether the front-end calls `updateUserRole` (a route no backend serves) and `getUserGroups` (no caller) are dead code (section 13.1).
- Whether the admin endpoints with no caller in the interface (a user's SSO sessions, group export, group member list) are meant for API use only (section 2).
- Whether the unused constant `New user signed up: {username}` is meant to be sent anywhere (section 9).
- Runtime confirmation: every behaviour in this document was read from the code, and none was exercised against a running instance.

### 14.5 Knowledgebase Consistency (Answered by the Knowledgebase Maintainer)

- `../tools/ground-truth.md` says model access control applies to non-admins unless `BYPASS_MODEL_ACCESS_CONTROL` is on; the code also applies it to admins while `BYPASS_ADMIN_ACCESS_CONTROL` is off (`backend/open_webui/main.py:1150`; `backend/open_webui/utils/models.py:526-528`). This does not contradict it under the code defaults, but the ground-truth wording may need that qualifier.
- Detail deferred to planned reference documents not yet written should be checked against this document when they exist: `sso-oauth-oidc-and-scim.md`, `workspace-models-and-model-access.md`, `admin-settings-panels.md`, `database-schema-identity-chats-and-config.md`, `user-settings-and-personalisation.md`, `notifications-webhooks-events-and-banners.md`, `channels-and-direct-messages.md`.
