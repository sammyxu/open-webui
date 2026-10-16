# Prompts (Slash Commands) and Skills

## At a Glance

- A **prompt** is a saved piece of text with a short command (for example `/summarize`). Typing `/` in the chat composer lists the prompts a user can see; choosing one inserts its text, after filling in any variables. Prompts live under **Workspace > Prompts** (`/workspace/prompts`). *Provisional; refined at the end of research.*
- A **skill** is a saved set of instructions (Markdown) that a model can read on demand. Skills live under **Workspace > Skills** (`/workspace/skills`) and are attached to models or chosen for a chat. *Provisional.*
- Both are governed by workspace permissions (`workspace.prompts`, `workspace.skills`) and per-item access grants; administrators bypass most checks. *Provisional.*
- Prompt text can contain variables such as `{{USER_NAME}}` or `{{CLIPBOARD}}` that are filled in when the prompt is used; some of them insert personal data. *Provisional.*
- *Checked 2026-10-09: the four bullets above were verified against the code; the bullets below were added when the document was completed.*
- **Commands are unique across the whole site**, including prompts the person cannot see or has switched off, which is what `Uh-oh! This command is already registered. Please choose another command string.` means (sections 5.3 and 11.2). The `/` list matches the command, not the name, and leaves out switched-off prompts (section 5.14).
- **Prompts keep versions; skills do not.** Each content save adds a version and one version is **Live**; restoring brings back the name, text and tags but not the command or sharing. Deleting a prompt or skill is permanent (sections 5.5, 5.6, 5.13, 5.23).
- **Using needs no workspace permission.** Anyone signed in can use prompts and skills shared with them; **Prompts Access** and **Skills Access** only open the workspace pages and allow creating. Saving re-applies sharing with the saver's own permissions (sections 3.1, 5.5, 5.19).
- **How a model gets a skill.** Switched on in the Integrations menu, attached to the model, or mentioned with `$`. With built-in tools on, the model sees a list of every active skill the person can read and loads one with `view_skill` only if it decides to; with them off, the chosen skills are sent in full. Read from code, a skill picked from the `/` list is not treated as a mention, and a model's default skills are added even when switched off (sections 5.24 to 5.26).
- **Personal data.** `{{USER_NAME}}`, `{{USER_EMAIL}}`, `{{USER_LOCATION}}`, `{{USER_BIO}}`, `{{USER_GENDER}}`, `{{USER_BIRTH_DATE}}` and `{{USER_AGE}}` fill in the details of the person using the prompt, in their own browser; prompt exports and change events carry owners' or actors' names and emails (sections 4.2, 5.10, 6.6, 9.1).
- **No local customisation** touches this area; the fork's **Hide Processing Details** setting hides `view_skill` calls in replies (section 12).

## 1. Purpose and Who Uses It

**Prompts** are saved pieces of text that people reuse in chats. Each prompt has a display name, a
short **command** (for example `summarize-paper`) and the prompt text. In the chat composer, typing
`/` opens a list that includes the prompts the person can see; choosing one replaces the typed
`/...` with the prompt text, after filling in any placeholders such as today's date or a value the
person types into a small form (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:77-85`,
`:442-475`; `src/lib/components/chat/MessageInput.svelte:631-686`). Prompts keep a **version
history**: every saved change becomes a version, one version is marked **Live** (the "production"
version), and an older version can be made live again (`backend/open_webui/models/prompts.py:23-39`;
`backend/open_webui/models/prompt_history.py:19-28`).

**Skills** are saved sets of instructions, written in Markdown, that a model reads when it needs
them, for example "how to review code in our house style". A skill has a name, an id (a short
lowercase slug such as `code-review-guidelines`), an optional one-line description and the
instructions (`backend/open_webui/models/skills.py:20-32`). A skill reaches the model in one of three
ways: the person switches it on for the chat (Integrations menu), the model has it attached as a
default, or the person mentions it in the message with `$`. The
model then either receives the full instructions or, when built-in tools are on, a short list of
available skills from which it loads the ones it needs with the `view_skill` tool
(`backend/open_webui/utils/middleware.py:2770-2905`; `backend/open_webui/tools/builtin.py:3482-3545`).
*Corrected 2026-10-09: the first version also counted picking a skill from the `/` list as a
mention. Read from code, a `/` pick is inserted without the `$` marker and the server does not
recognize it as a skill mention (section 5.25). It also left out that, with built-in tools on, the
short list names every active skill the person can read, switched on or not (section 5.26).*
Skills have no version history.

Both live in the **Workspace**, alongside models, knowledge and tools, and both are owned by the
person who created them and can be shared with people or groups.

**Who uses this area**

| Who | What they do here | Source |
|---|---|---|
| Any signed-in user (role `user` or `admin`) | Uses prompts with `/` and skills with `$`, the Integrations menu, or model defaults, limited to items they own or that are shared with them. No workspace permission is needed to *use* a shared prompt or skill in a chat | `backend/open_webui/routers/prompts.py:54-61`; `backend/open_webui/routers/skills.py:39-55`, `:63-115` |
| Users with the **Prompts Access** permission (`workspace.prompts`) | Open Workspace › Prompts; create, edit, version, share, clone and delete their own prompts and prompts shared with them for writing | `src/routes/(app)/workspace/+layout.svelte:51`, `:89-93`; `backend/open_webui/routers/prompts.py:150-167` |
| Users with the **Skills Access** permission (`workspace.skills`) | Open Workspace › Skills; create, edit, share, clone, switch on or off and delete skills | `src/routes/(app)/workspace/+layout.svelte:52`, `:99-100`; `backend/open_webui/routers/skills.py:158-165` |
| Admins | Everything above without the workspace permissions; by default (admin bypass) they also see and can change every prompt and skill (section 3) | `backend/open_webui/routers/prompts.py:56`, `:103`; `backend/open_webui/routers/skills.py:46`, `:88` |
| Model owners | Attach skills to a workspace model so they are switched on by default (`meta.skillIds`); described in `workspace-models-and-model-access.md` | `src/lib/components/workspace/Models/ModelEditor.svelte:353-358`, `:1203` |
| Tier 1 support | Explains how prompts, variables and skills behave, reads what a person sees, and escalates permission, sharing or data questions. Tier 1 does not change prompts, skills, permissions or sharing | Research instructions (rule 14) |

**Not in this area.** The example cards on the new-chat screen are **prompt suggestions**, not
workspace prompts (section 4.3); they are covered in `chat-composer-and-message-display.md` and
`workspace-models-and-model-access.md`. The composer itself (other `/` commands, `#`, `@`, `:`) is
covered in `chat-composer-and-message-display.md`; the `view_skill` tool in `builtin-native-tools.md`;
terminal skills come from a connected terminal server (`workspace-tools-tool-servers-mcp-and-terminals.md`).

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Pages

| Path | What it shows | Who can open it | Source |
|---|---|---|---|
| Sidebar › **Workspace** (`/workspace`) | Link shown to admins and to anyone with at least one workspace permission (models, knowledge, prompts, tools or skills). `/workspace` itself only redirects: admins go to `/workspace/models`; others go to the first section they may use, in the order Models, Knowledge, Prompts, Tools, Skills, or to `/` | As described | `src/lib/components/layout/Sidebar.svelte:164-172`; `src/routes/(app)/workspace/+page.svelte:1-24` |
| `/workspace/prompts` | The prompt list: search box `Search Prompts`, a view filter, a tag filter (only when some prompt has tags), columns **Title** and **Updated at**, 30 prompts per page | Admins, and users with `workspace.prompts` | `src/routes/(app)/workspace/prompts/+page.svelte:1-5`; `src/lib/components/workspace/Prompts.svelte:448-756` |
| `/workspace/prompts/create` | The same list with the **Create Prompt** dialog already open; closing the dialog returns to `/workspace/prompts` | Same | `src/routes/(app)/workspace/prompts/create/+page.svelte:1-5`; `src/lib/components/workspace/Prompts.svelte:240-247`, `:330-332` |
| `/workspace/prompts/{id}` | One prompt: name and command at the top, tags, the prompt id (click to copy), a **History** column and the content of the selected version. Editable for the owner and people with write access; otherwise marked `Read Only` | Anyone who can read the prompt and is allowed into the Prompts section | `src/routes/(app)/workspace/prompts/[id]/+page.svelte:42-71`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:391-548` |
| `/workspace/skills` | The skill list: search box `Search Skills`, a view filter, columns **Title** and **Updated at**, 30 skills per page | Admins, and users with `workspace.skills` | `src/routes/(app)/workspace/skills/+page.svelte:1-5`; `src/lib/components/workspace/Skills.svelte:334-615` |
| `/workspace/skills/create` | The skill editor for a new skill. Also opened, pre-filled, by **Clone** and by importing a Markdown file | Same | `src/routes/(app)/workspace/skills/create/+page.svelte:1-57` |
| `/workspace/skills/edit?id={id}` | The skill editor for an existing skill (the id is in the query string, not the path) | Anyone who can read the skill and is allowed into the Skills section | `src/routes/(app)/workspace/skills/edit/+page.svelte:17`, `:42-71` |

**Workspace tab bar.** The top of every workspace page shows tabs **Models**, **Knowledge**,
**Prompts**, **Skills** and **Tools**, each with a count of items on the person's list, and only for
the sections the person may use (Tools also needs plugins switched on). A split button on the right
holds the page's actions; on the prompt and skill lists these are **Create**, **Import JSON** and
**Export JSON**, each shown only when allowed (section 3)
(`src/routes/(app)/workspace/+layout.svelte:48-78`, `:185-238`;
`src/lib/components/workspace/Prompts.svelte:92-127`; `src/lib/components/workspace/Skills.svelte:73-105`).

**Redirects.** A non-admin who opens a `/workspace/prompts...` address without `workspace.prompts`,
or a `/workspace/skills...` address without `workspace.skills`, is sent to `/` without a message
(`src/routes/(app)/workspace/+layout.svelte:80-102`). A prompt or skill page that cannot be loaded
(missing, or no read access) shows the server's message in a pop-up and returns to the list
(`src/routes/(app)/workspace/prompts/[id]/+page.svelte:44-62`;
`src/routes/(app)/workspace/skills/edit/+page.svelte:44-62`).

**Browser tab titles** read `Prompts / {site name}`, `Skills / {site name}` and
`Workspace / {site name}`, where the site name is `WEBUI_NAME` (MedIT GPT by default)
(`src/lib/components/workspace/Prompts.svelte:372-374`; `src/lib/components/workspace/Skills.svelte:262-264`;
`src/routes/(app)/workspace/+layout.svelte:112-114`).

### 2.2 Where Prompts and Skills Appear in a Chat

| Place | What it does | Source |
|---|---|---|
| `/` in the composer | A pop-up with up to three groups: `Commands` (built-in commands such as `/model`), `Prompts` (prompts whose **command** contains what was typed after `/`, sorted by name, showing command and name) and `Skills` | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:53-85`, `:174-518` |
| `$` in the composer | A pop-up headed `Skills` listing skills whose name, description, id or owner matches what was typed; terminal skills are labelled `Terminal` | `src/lib/components/chat/MessageInput/Commands/Skills.svelte:41-62`, `:103-143`; `backend/open_webui/models/skills.py:233-243` |
| **Integrations** menu (puzzle-piece button) › **Skills** | A searchable list (`Search skills`) of active skills with a switch each; switched-on skills are sent with every message in this chat | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:167-189`, `:337-357`, `:655-731` |
| Skills chip (cube icon and a number) | Appears under the composer when at least one skill is switched on; tooltip `{COUNT} Available Skills`; clicking opens the **Available Skills** dialog listing their names and descriptions | `src/lib/components/chat/MessageInput.svelte:2390-2412`; `src/lib/components/chat/SkillsModal.svelte:22-66` |
| New chat with one model selected | The model's default skills (if active and visible to the person) are switched on automatically | `src/lib/components/chat/Chat.svelte:1062-1073` |

### 2.3 API Endpoints

All are under the backend's `/api/v1` prefix and need a signed-in account with role `user` or
`admin` (`get_verified_user`) (`backend/open_webui/main.py:868`, `:870`). Listed for diagnosis only;
tier 1 does not call them.

| Method and path | Purpose | Source |
|---|---|---|
| `GET /api/v1/prompts/` | Active prompts the person can read (all active prompts for an admin with admin bypass). Used by the `/` list and by **Export JSON** | `backend/open_webui/routers/prompts.py:54-61` |
| `GET /api/v1/prompts/tags` | Tags of active prompts the person can read | `backend/open_webui/routers/prompts.py:64-68` |
| `GET /api/v1/prompts/list` | One page (30) of the workspace list, active and inactive, with search, view, tag and sort filters and a `write_access` flag per prompt | `backend/open_webui/routers/prompts.py:71-135` |
| `POST /api/v1/prompts/create` | Create a prompt (also used by import and clone) | `backend/open_webui/routers/prompts.py:143-197` |
| `GET /api/v1/prompts/id/{prompt_id}` | One prompt with `write_access` | `backend/open_webui/routers/prompts.py:205-241` |
| `POST /api/v1/prompts/id/{prompt_id}/update` | Save content (creates a version) | `backend/open_webui/routers/prompts.py:249-315` |
| `POST /api/v1/prompts/id/{prompt_id}/update/meta` | Save name, command and tags only (no version) | `backend/open_webui/routers/prompts.py:323-381` |
| `POST /api/v1/prompts/id/{prompt_id}/update/version` | Make a version live (restores its content) | `backend/open_webui/routers/prompts.py:384-429` |
| `POST /api/v1/prompts/id/{prompt_id}/access/update` | Replace sharing | `backend/open_webui/routers/prompts.py:441-490` |
| `POST /api/v1/prompts/id/{prompt_id}/toggle` | Switch the prompt on or off | `backend/open_webui/routers/prompts.py:498-543` |
| `DELETE /api/v1/prompts/id/{prompt_id}/delete` | Delete the prompt and its whole history | `backend/open_webui/routers/prompts.py:551-591` |
| `GET /api/v1/prompts/id/{prompt_id}/history?page={n}` | Versions, newest first, 20 per page (pages start at 0) | `backend/open_webui/routers/prompts.py:599-635` |
| `GET /api/v1/prompts/id/{prompt_id}/history/{history_id}` | One version | `backend/open_webui/routers/prompts.py:638-678` |
| `DELETE /api/v1/prompts/id/{prompt_id}/history/{history_id}` | Delete one version (not the live one) | `backend/open_webui/routers/prompts.py:681-728` |
| `GET /api/v1/prompts/id/{prompt_id}/history/diff?from_id=&to_id=` | Line-by-line difference of two versions' content. The interface does not call it (section 14) | `backend/open_webui/routers/prompts.py:731-772` |
| `GET /api/v1/skills/` | Every skill the person can read, active or not (all skills for an admin with admin bypass); optional `query` matches the name | `backend/open_webui/routers/skills.py:39-55` |
| `GET /api/v1/skills/list` | One page (30) of the workspace list with search, view and sort filters and `write_access`; also feeds the `/` and `$` lists | `backend/open_webui/routers/skills.py:63-115` |
| `GET /api/v1/skills/export` | Full skills (including instructions) for **Export JSON**; needs `workspace.skills_export` or admin | `backend/open_webui/routers/skills.py:123-143` |
| `POST /api/v1/skills/create` | Create a skill (also used by JSON import and clone) | `backend/open_webui/routers/skills.py:151-219` |
| `GET /api/v1/skills/id/{id}` | One skill with `write_access` | `backend/open_webui/routers/skills.py:227-266` |
| `POST /api/v1/skills/id/{id}/update` | Save a skill | `backend/open_webui/routers/skills.py:274-345` |
| `POST /api/v1/skills/id/{id}/access/update` | Replace sharing | `backend/open_webui/routers/skills.py:357-406` |
| `POST /api/v1/skills/id/{id}/toggle` | Switch the skill on or off | `backend/open_webui/routers/skills.py:414-459` |
| `DELETE /api/v1/skills/id/{id}/delete` | Delete the skill | `backend/open_webui/routers/skills.py:467-506` |

The browser calls these through `src/lib/apis/prompts/index.ts` and `src/lib/apis/skills/index.ts`.
When creating a prompt, the browser removes a leading `/` from the command before sending it
(`src/lib/apis/prompts/index.ts:48-62`).

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending`; pending accounts cannot use the application, so they never
reach prompts or skills (`knowledgebase/tools/ground-truth.md`, Accounts and Access). How permission
values combine across groups, and the share dialog itself, are described in
`users-groups-roles-and-permissions.md` (sections 3, 5.16 and 5.17); this section lists only what
applies to prompts and skills.

### 3.1 Permission Keys

All ten keys are **off in code** for ordinary users. Admins set the defaults (Admin Panel › Users ›
Groups, "default permissions") and per group; the live values are data and **TO BE CONFIRMED**
(`backend/open_webui/config.py:1940-1966`).

| Key | Label in the admin permissions editor | Environment variable (seeds the default) | What it controls | Checked by the server? | Source |
|---|---|---|---|---|---|
| `workspace.prompts` | **Prompts Access** | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS` | The Prompts tab and pages; creating prompts | Yes, on create only (either this key or `workspace.prompts_import`) | `backend/open_webui/config.py:1741-1742`; `src/lib/components/admin/Users/Groups/Permissions.svelte:106-108`; `backend/open_webui/routers/prompts.py:150-167` |
| `workspace.prompts_import` | **Import Prompts** (shown under Prompts Access when that is on) | `USER_PERMISSIONS_WORKSPACE_PROMPTS_IMPORT` | **Import JSON** on the prompt list | Yes: it also allows creating prompts on its own | `backend/open_webui/config.py:1761-1762`; `src/lib/components/admin/Users/Groups/Permissions.svelte:111-121`; `src/lib/components/workspace/Prompts.svelte:102-107` |
| `workspace.prompts_export` | **Export Prompts** | `USER_PERMISSIONS_WORKSPACE_PROMPTS_EXPORT` | **Export JSON** on the list and **Export** in each prompt's menu | No: both exports read lists any signed-in user may read | `backend/open_webui/config.py:1765-1766`; `src/lib/components/workspace/Prompts.svelte:108-125`; `src/lib/components/workspace/Prompts/PromptMenu.svelte:96-108` |
| `sharing.prompts` | **Prompts Sharing** | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_SHARING` | The **Access List** in a prompt's Access dialog | No (interface only) | `backend/open_webui/config.py:1802-1803`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:295-299` |
| `sharing.public_prompts` | **Prompts Public Sharing** | `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING` | The **Public** choice for prompts | Yes: a public grant is silently removed without it | `backend/open_webui/config.py:1806-1807`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:300`; `backend/open_webui/routers/prompts.py:169-175`, `:292-298`, `:472-478` |
| `workspace.skills` | **Skills Access**, with the hover warning `Warning: Enabling this will allow users to upload arbitrary code on the server.` | `USER_PERMISSIONS_WORKSPACE_SKILLS_ACCESS` | The Skills tab and pages; the **Create** action; creating skills | Yes, on create only (either this key or `workspace.skills_import`) | `backend/open_webui/config.py:1749-1750`; `src/lib/components/admin/Users/Groups/Permissions.svelte:186-198`; `src/lib/components/workspace/Skills.svelte:75-80`; `backend/open_webui/routers/skills.py:158-165` |
| `workspace.skills_import` | **Import Skills** | `USER_PERMISSIONS_WORKSPACE_SKILLS_IMPORT` | **Import JSON** on the skill list (JSON or Markdown files) | Yes: it also allows creating skills on its own | `backend/open_webui/config.py:1777-1778`; `src/lib/components/admin/Users/Groups/Permissions.svelte:201-211`; `src/lib/components/workspace/Skills.svelte:81-86` |
| `workspace.skills_export` | **Export Skills** | `USER_PERMISSIONS_WORKSPACE_SKILLS_EXPORT` | **Export JSON** on the list and **Export** in each skill's menu | Partly: the list export is refused without it; the single-skill export reads the skill like the editor does | `backend/open_webui/config.py:1781-1782`; `backend/open_webui/routers/skills.py:129-138`; `src/lib/components/workspace/Skills.svelte:87-103`, `:192-204`; `src/lib/components/workspace/Skills/SkillMenu.svelte:78-89` |
| `sharing.skills` | **Skills Sharing** | `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_SHARING` | The **Access List** in a skill's Access dialog | No (interface only) | `backend/open_webui/config.py:1819-1820`; `src/lib/components/workspace/Skills/SkillEditor.svelte:93-97` |
| `sharing.public_skills` | **Skills Public Sharing** | `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_PUBLIC_SHARING` | The **Public** choice for skills | Yes: a public grant is silently removed without it | `backend/open_webui/config.py:1823-1824`; `src/lib/components/workspace/Skills/SkillEditor.svelte:98`; `backend/open_webui/routers/skills.py:188-194`, `:310-316`, `:388-394` |

Sharing with named people and with groups additionally needs `access_grants.allow_users` and
`access_grants.allow_groups` (on by default in the interface when unset); the server removes person or
group entries the sharer may not add (`src/lib/components/workspace/Prompts/PromptEditor.svelte:301-302`;
`src/lib/components/workspace/Skills/SkillEditor.svelte:99-100`;
`backend/open_webui/utils/access_control/__init__.py:277-299`). Prompts and skills cannot be made
**Open** ("anyone with the link"): such an entry is always removed, even for admins, because neither
router passes a permission key for it (`backend/open_webui/utils/access_control/__init__.py:239-251`;
`backend/open_webui/routers/prompts.py:169-175`; `backend/open_webui/routers/skills.py:188-194`).

**Using is not gated by these keys.** The `/` list, the `$` list and the Integrations menu read
prompts and skills through endpoints that any signed-in user may call, so a person without Prompts
Access or Skills Access can still use prompts and skills that are shared with them
(`backend/open_webui/routers/prompts.py:54-61`; `backend/open_webui/routers/skills.py:39-55`,
`:63-115`; `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:119-131`).

**Removing Prompts Access or Skills Access hides the pages but does not lock the person out of their
own items.** The server checks these keys only when something is created; editing, switching off,
sharing and deleting are checked against ownership and write access instead
(`backend/open_webui/routers/prompts.py:266-281`; `backend/open_webui/routers/skills.py:289-303`).

### 3.2 Ownership and Per-Item Access

| Who | Prompts | Skills | Source |
|---|---|---|---|
| Owner (creator) | Full control, always, without a grant | Same | `backend/open_webui/models/access_grants.py:759-761`; `backend/open_webui/routers/prompts.py:266-281`; `backend/open_webui/routers/skills.py:289-303` |
| Person or group with **Read** | Sees the prompt in the `/` list and the workspace list (marked `Read Only`), opens it read-only with its history, can copy, clone and (with the permission) export it | Sees and uses the skill; opens it read-only; no menu or switch in the list | `backend/open_webui/routers/prompts.py:205-241`, `:599-635`; `src/lib/components/workspace/Prompts.svelte:606-608`; `src/lib/components/workspace/Skills.svelte:483-485`, `:521` |
| Person or group with **Write** | Everything the owner can do: edit content, name, command and tags, make versions live, delete versions, change sharing, switch off, **delete** | Edit, change sharing, switch on or off, **delete** | `backend/open_webui/routers/prompts.py:266-281`, `:399-413`, `:456-470`, `:513-527`, `:566-580`, `:697-712`; `backend/open_webui/routers/skills.py:372-386`, `:422-433`, `:481-495` |
| **Public** (`user:*` read grant) | Every signed-in user can read and use it | Same | `backend/open_webui/models/access_grants.py:750-757` |
| Admin, admin bypass on (code default) | Sees every prompt in the list and in the `/` list, all marked writable | Sees every skill in the list, `/` and `$` lists; the list export includes every skill | `backend/open_webui/routers/prompts.py:56-57`, `:103-130`; `backend/open_webui/routers/skills.py:46-47`, `:88-110`, `:140-141`; `backend/open_webui/config.py:2086-2092` |
| Admin, admin bypass off | Lists show only own and shared items; other items open as `Read Only` in the interface, but the server still accepts the admin's edits, version changes, sharing changes and deletions | Same pattern | `backend/open_webui/routers/prompts.py:211-235`, `:266-281`; `backend/open_webui/routers/skills.py:231-256`, `:289-303` |

**Skills in a chat follow the person's own access, including for admins.** When a message is sent,
the server resolves skills with the person's ownership and grants; there is no admin bypass on this
path, so a skill an admin can see only because of admin bypass is not added to the admin's chats.
The `view_skill` tool, by contrast, lets an admin load any active skill by id
(`backend/open_webui/utils/middleware.py:2830-2839`; `backend/open_webui/models/skills.py:179-188`;
`backend/open_webui/tools/builtin.py:3523-3534`). Confirming this in a test environment is listed in
section 14.

The interface shows a prompt's **Delete**, **Clone**, **Export** and on/off switch to everyone who
can see it, including read-only viewers; the server then refuses the change
(`src/lib/components/workspace/Prompts.svelte:640-735`; `src/lib/components/workspace/Prompts/PromptMenu.svelte:44-122`).
The skill list hides the menu and switch from read-only viewers
(`src/lib/components/workspace/Skills.svelte:521-595`).

## 4. Key Concepts and Terminology

### 4.1 Prompt Terms

| Term | Meaning | Source |
|---|---|---|
| **Prompt** | A saved text template owned by one person: a name, a command, the text (content), optional tags, an on/off flag and a version history. Stored in the `prompt` table (section 6) | `backend/open_webui/models/prompts.py:23-39` |
| **Command** | The word typed after `/` to find the prompt, stored without the `/`. It is **unique across the whole site, for all users**: a second prompt cannot use a command that anyone else already uses, even one the person cannot see (`COMMAND_TAKEN`, section 10). The uniqueness check compares the stored text exactly | `backend/open_webui/models/prompts.py:29`, `:190-196`; `backend/open_webui/routers/prompts.py:177-197`, `:283-290` |
| **Command characters** | The prompt editor accepts only letters, digits, hyphens and underscores (`^[a-zA-Z0-9-_]+$`), although its message mentions only "alphanumeric characters and hyphens". While a new prompt is being created, the command is suggested from the name (accents removed, spaces become hyphens, other characters dropped, lower case) until the person types in the command box. The server itself does not check the characters, so commands arriving by JSON import are stored as they are in the file | `src/lib/components/workspace/Prompts/PromptEditor.svelte:74-80`, `:112-124`; `src/lib/utils/index.ts:1699-1713`; `src/lib/components/workspace/Prompts.svelte:424-434` |
| **Name** | The display name (the list's **Title** column). Older Open WebUI exports called it `title`; clone and the community-site import accept either, the JSON import reads only `name` | `backend/open_webui/models/prompts.py:31`, `:85`; `src/lib/components/workspace/Prompts.svelte:227-233`, `:426-430` |
| **Content** | The prompt text, with optional placeholders (section 4.2) | `backend/open_webui/models/prompts.py:32` |
| **Tags** | Free-text labels used by the list's **Tag** filter. Tag suggestions come from tags on prompts the person can read | `backend/open_webui/models/prompts.py:35`, `:682-721`; `src/lib/components/workspace/Prompts.svelte:501-511`; `src/lib/components/workspace/common/TagSelector.svelte:12` |
| **Enabled / Disabled** (`is_active`) | The switch on each list row. A disabled prompt stays in the workspace list but is left out of the `/` list, out of **Export JSON** and out of the tag list | `backend/open_webui/models/prompts.py:36`, `:200-211`, `:247`, `:685`; `src/lib/components/workspace/Prompts.svelte:713-733` |
| **Version** (history entry) | A snapshot of the prompt (name, content, command, tags, sharing, plus internal `data` and `meta`) with an author, a time and an optional commit message. Versions form a chain through a parent link | `backend/open_webui/models/prompt_history.py:19-28`; `backend/open_webui/models/prompts.py:146-165`, `:530-547` |
| **Live / production version** | The version the prompt currently uses (`version_id`). It is labelled `Live` in the History column and cannot be deleted | `backend/open_webui/models/prompts.py:37`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:501-512`, `:704-710`; `backend/open_webui/routers/prompts.py:714-719` |
| **Commit message** | Optional note saved with a version. The first version gets `Initial version` when none is given; later versions without one are listed as `Update` | `backend/open_webui/models/prompts.py:163`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:347-357`, `:701-703` |
| **Set as Production** | A tick box in the **Edit Prompt** dialog (ticked by default) and a link on any non-live version. Unticked, the save becomes a version that is not live, and the prompt keeps its current text | `src/lib/components/workspace/Prompts/PromptEditor.svelte:359-369`, `:505-511`; `backend/open_webui/models/prompts.py:511-518`, `:549-552` |
| **Read Only** | Badge on prompts the person cannot change | `src/lib/components/workspace/Prompts.svelte:606-608`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:439-443` |
| **View filter** | `All`, `Created by you` or `Shared with you`; remembered in the browser and shared by the workspace sections | `src/lib/components/workspace/common/ViewSelector.svelte:16-18`; `src/lib/components/workspace/Prompts.svelte:309`, `:491-499`; `backend/open_webui/models/prompts.py:314-318` |
| **Search** | The list search matches the prompt's name, command and text, and the owner's name and email | `backend/open_webui/models/prompts.py:301-312` |

### 4.2 Prompt Variables (Placeholders)

When a prompt is inserted into the composer (from the `/` list, and also when text is placed in the
composer from a suggestion card or a follow-up), the browser first fills in the built-in
placeholders below, then looks for any remaining `{{...}}` placeholders and, if there are any, opens
the **Input Variables** form (`src/lib/components/chat/MessageInput.svelte:263-402`, `:419-439`,
`:594-629`, `:631-686`). Everything happens in the person's own browser and the result is visible
in the composer before it is sent; once sent it is part of the message, the saved chat and anything
the chat is later shared or exported with.

**Built-in placeholders**

| Placeholder | Replaced with | Personal data? | When the value is missing | Source |
|---|---|---|---|---|
| `{{CLIPBOARD}}` | The text currently on the clipboard (the browser asks for permission). Any image on the clipboard is also attached to the message as a file | Whatever the person copied | Error `Failed to read clipboard contents`; the placeholder stays and is then asked for in the Input Variables form as `CLIPBOARD` | `src/lib/components/chat/MessageInput.svelte:284-309` |
| `{{USER_LOCATION}}` | The browser's location as latitude and longitude to three decimals, followed by `(lat, long)` | Yes (location) | Error `Location access not allowed`; inserts `LOCATION_UNKNOWN` | `src/lib/components/chat/MessageInput.svelte:311-320`; `src/lib/utils/index.ts:794-815` |
| `{{USER_NAME}}` | The account's name | Yes | `User` | `src/lib/components/chat/MessageInput.svelte:322-327` |
| `{{USER_EMAIL}}` | The account's email address | Yes | Left as is (then asked for in the form) | `src/lib/components/chat/MessageInput.svelte:329-335` |
| `{{USER_BIO}}` | The profile's bio | Yes | Left as is (then asked for) | `src/lib/components/chat/MessageInput.svelte:337-343` |
| `{{USER_GENDER}}` | The profile's gender | Yes | Left as is (then asked for) | `src/lib/components/chat/MessageInput.svelte:345-351` |
| `{{USER_BIRTH_DATE}}` | The profile's date of birth | Yes | Left as is (then asked for) | `src/lib/components/chat/MessageInput.svelte:353-359` |
| `{{USER_AGE}}` | Age in whole years, computed from the date of birth | Yes | Left as is (then asked for) | `src/lib/components/chat/MessageInput.svelte:361-369`; `src/lib/utils/index.ts:2098-2108` |
| `{{USER_LANGUAGE}}` | The interface language code saved in the browser | No | `en-US` | `src/lib/components/chat/MessageInput.svelte:371-374` |
| `{{CURRENT_DATE}}` | Today's date as `YYYY-MM-DD`, from the computer's clock | No | n/a | `src/lib/components/chat/MessageInput.svelte:376-379`; `src/lib/utils/index.ts:1393-1400` |
| `{{CURRENT_TIME}}` | The time as `HH:MM:SS` (24-hour) | No | n/a | `src/lib/components/chat/MessageInput.svelte:381-384`; `src/lib/utils/index.ts:1402-1406` |
| `{{CURRENT_DATETIME}}` | Date and time together | No | n/a | `src/lib/components/chat/MessageInput.svelte:386-389`; `src/lib/utils/index.ts:1408-1411` |
| `{{CURRENT_TIMEZONE}}` | The computer's time zone name (for example `America/Toronto`) | No | n/a | `src/lib/components/chat/MessageInput.svelte:391-394`; `src/lib/utils/index.ts:1413-1416` |
| `{{CURRENT_WEEKDAY}}` | The English weekday name | No | n/a | `src/lib/components/chat/MessageInput.svelte:396-399`; `src/lib/utils/index.ts:1418-1423` |

The name, email, bio, gender and date of birth come from the person's own account, read fresh from
the server each time (`src/lib/components/chat/MessageInput.svelte:322`;
`backend/open_webui/routers/auths.py:243-249`). A prompt shared by someone else therefore fills in
the *user's* details, not the author's. The prompt list's search does not reveal these values; they
exist only in the composer of the person using the prompt.

**Custom input variables.** Any other placeholder becomes a field in the **Input Variables** form
(`src/lib/utils/index.ts:1731-1751`, `:1805-1862`; `src/lib/components/chat/MessageInput/InputVariablesModal.svelte`):

- `{{topic}}` gives a free-text field labelled `topic`. A variable name cannot contain spaces, `|`
  or `}`.
- `{{name | type}}` or `{{name | type:property=value:flag}}` chooses a field type and options, for
  example `{{audience | select:options=["Residents","Faculty"]:required}}` or
  `{{rotation_start | date:required}}` (invented examples).
- Types: `text`, `select` (with `options=[...]`), `checkbox`, `color`, `date`, `datetime-local`,
  `email`, `month`, `number`, `range`, `tel`, `time`, `url` and `map`; any other type shows a
  multi-line box. The `map` type is marked in the code as experimental and "DO NOT USE IN
  PRODUCTION" (`src/lib/components/chat/MessageInput/InputVariablesModal.svelte:123-352`, `:322`).
- Properties: `required` (shows `* required` and blocks **Save** until filled), `default=...`,
  `placeholder=...`, `label=...`; other properties such as `min=` or `max=` are passed to the field
  (`src/lib/components/chat/MessageInput/InputVariablesModal.svelte:25`, `:43-56`, `:108`, `:115-117`).
- **Save** replaces the placeholders everywhere in the composer, including any matching
  placeholder that was already there; **Cancel** or closing the form leaves the `{{...}}` text in
  the composer to be edited by hand (`src/lib/components/common/RichTextInput.svelte:581-620`;
  `src/lib/components/chat/MessageInput.svelte:263-281`).

**The same names mean something slightly different in system prompts.** Model and personal system
prompts are filled in on the server, with `Unknown` when a value is missing and an extra
`{{USER_GROUPS}}` placeholder; that is part of the chat pipeline
(`backend/open_webui/utils/task.py:36-104`; `backend/open_webui/utils/payload.py:25-41`;
`chat-completion-pipeline-and-generation-tasks.md`), not of workspace prompts.

### 4.3 Prompt Suggestions Are Not Prompts

The cards under the composer on a new chat (for example `Help me study`) are **prompt suggestions**:
a title, a subtitle and text, set by an admin for all models (`ui.prompt_suggestions`, seeded from
`DEFAULT_PROMPT_SUGGESTIONS`) or per model. They are not stored in the `prompt` table, have no
command and are not shown under Workspace › Prompts. Clicking one goes through the same placeholder
handling as a prompt (`backend/open_webui/config.py:1678-1685`, `:3091-3092`;
`backend/open_webui/routers/configs.py:806-840`; `src/lib/components/chat/MessageInput.svelte:419-439`).
Details: `chat-composer-and-message-display.md` (section 5.1) and
`workspace-models-and-model-access.md`.

### 4.4 Skill Terms

| Term | Meaning | Source |
|---|---|---|
| **Skill** | Markdown instructions a model can follow, with a name, id and description; owned and shareable like a prompt. Stored in the `skill` table | `backend/open_webui/models/skills.py:20-32` |
| **Skill ID** | The skill's permanent identifier, shown in lists after a `/` (for example `/code-review-guidelines`). Suggested from the name while typing; the server lower-cases it, turns spaces into hyphens and then accepts only lower-case letters, digits, `-` and `_`. It must be unique and cannot be changed after creation | `src/lib/components/workspace/Skills/SkillEditor.svelte:37-39`, `:63`, `:140-161`; `backend/open_webui/routers/skills.py:167-181`, `:319-321` |
| **Skill name** | The display name. It must also be unique across the site: the database refuses a second skill with the same name | `backend/open_webui/models/skills.py:25`; `backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_skill_table.py:29` |
| **Description** | One line shown in lists and given to the model in the list of available skills | `backend/open_webui/models/skills.py:26`; `backend/open_webui/utils/middleware.py:2851-2854` |
| **Instructions** (content) | The Markdown body. If it starts with a front-matter block (`---` lines containing `name:` and `description:`), the editor copies those into empty name and description fields while a new skill is written | `src/lib/components/workspace/Skills/SkillEditor.svelte:41-50`, `:193-208`; `src/lib/utils/index.ts:2448-2468` |
| **Translations** | Optional per-language name and description (`meta.i18n`), edited with the language selector in the editor and shown to people using that interface language | `backend/open_webui/models/skills.py:35-37`; `src/lib/components/workspace/Skills/SkillEditor.svelte:129-182`; `src/lib/utils/localizedContent.ts:20-44` |
| **Active / Inactive** (`is_active`) | The switch on each list row; inactive skills carry an `Inactive` badge. The server ignores inactive skills in chats and `view_skill` reports them as not found; the Integrations menu and model defaults leave them out. The `/` and `$` pop-ups still list them | `backend/open_webui/models/skills.py:29`; `src/lib/components/workspace/Skills.svelte:479-481`; `backend/open_webui/utils/middleware.py:2836-2839`; `backend/open_webui/tools/builtin.py:3520-3521`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:167-175`; `src/lib/components/chat/Chat.svelte:1063-1070`; `backend/open_webui/models/skills.py:219-259` |
| **Skill mention** | Picking a skill from `$` puts a chip such as `$Code Review Guidelines` in the composer; the message text carries it as `<$code-review-guidelines\|Code Review Guidelines>`. Picking a skill from the `/` list in a chat puts an `@Code Review Guidelines` chip instead, carried as `<@code-review-guidelines\|Code Review Guidelines>`, which the server does not treat as a skill mention (read from code, section 5.25). *Corrected 2026-10-09: the first version said `$` and `/` picks behave the same; the chat composer's own `/` handler inserts the chip without the `$` marker, so the editor's default `@` applies* | `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:141-151`, `:218-237`; `src/lib/components/common/RichTextInput.svelte:117-127`, `:297-302`; `src/lib/components/chat/MessageInput.svelte:1427-1460`, `:1554-1564`; `backend/open_webui/utils/skills.py:8-10` |
| **Selected skills** | Skills switched on in the Integrations menu (or pre-selected from the model); sent with each message as `skill_ids` | `src/lib/components/chat/Chat.svelte:3568-3593` |
| **Model default skills** | Skills attached to a workspace model (`meta.skillIds`), pre-selected when that model alone is chosen | `src/lib/components/workspace/Models/ModelEditor.svelte:353-358`; `src/lib/components/chat/Chat.svelte:1062-1073` |
| **Available skills list** | When built-in tools are on, the model is given `<available_skills>` (id, name and description of each skill the person may use) and the `view_skill` tool to load one | `backend/open_webui/utils/middleware.py:2841-2905`; `backend/open_webui/utils/tools.py:734-736` |
| **Terminal skill** | A skill stored on a connected Open Terminal server rather than in MedIT GPT; ids start with `terminal:` and lists label them `Terminal` | `backend/open_webui/utils/middleware.py:2826-2898`; `src/lib/components/chat/MessageInput/Commands/Skills.svelte:136-138` |
| **`/skills:create`** | A composer command, offered only with a terminal selected and some chat content, that asks the model to write a new terminal skill (a `SKILL.md` file on the terminal), not a workspace skill | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:72-74`; `backend/open_webui/utils/skills.py:35`, `:81-115`, `:147-167` |
| **`view_skill`** | The built-in tool the model calls to load the full instructions of one skill named in the available-skills list. It answers with the skill's name and instructions, or with `Skill '{id}' not found` (unknown or inactive) or `Access denied` (section 10.6) | `backend/open_webui/tools/builtin.py:3482-3545`; `backend/open_webui/utils/tools.py:734-736` |
| **Skill tags** (`meta.tags`) | A list field in a skill's metadata. No screen in this release shows or edits it; the editor keeps whatever the field already holds (for example from a JSON import) | `backend/open_webui/models/skills.py:35-37`; `src/lib/components/workspace/Skills/SkillEditor.svelte:66-74`, `:80-89` |

## 5. Workflows (Step by Step)

Each workflow names what the person does, what the code does in response and what can go wrong. The
messages quoted here are listed with their triggers in section 10; permissions are in section 3.
Tier 1 follows these steps only to explain and diagnose; it does not change prompts, skills, sharing
or permissions.

### 5.1 Find and Browse Prompts

1. Open **Workspace › Prompts** (`/workspace/prompts`). The page needs **Prompts Access** or the admin
   role (section 3.1).
2. The list shows 30 prompts per page, most recently changed first. Each row shows the name, the
   command after a `/`, how long ago it changed (hover for the full date), a `Read Only` badge when the
   person cannot change it, the start of the prompt text, the owner's name on wider screens (hover shows
   the owner's email; `Deleted User` when the account no longer exists), a **Copy Prompt** button that
   copies the text, the **...** menu and the on/off switch
   (`src/lib/components/workspace/Prompts.svelte:559-738`, `:742-746`).
3. **Search Prompts** filters after a 0.3-second pause; it matches the name, command and text, and the
   owner's name and email (`src/lib/components/workspace/Prompts.svelte:129-139`;
   `backend/open_webui/models/prompts.py:301-312`).
4. The view filter (`All`, `Created by you`, `Shared with you`) and, when any readable prompt has tags,
   the **Tag** filter narrow the list. Clicking **Title** or **Updated at** sorts by that column; a
   second click reverses the order (`src/lib/components/workspace/Prompts.svelte:142-160`, `:491-511`).
5. Disabled prompts stay in this list with their switch off (section 5.8). Nothing matching shows
   `No prompts found` with `Try adjusting your search or filter to find what you are looking for.`
   (`src/lib/components/workspace/Prompts.svelte:747-756`).
6. Clicking a row opens the prompt page, `/workspace/prompts/{id}` (`:162-164`).

### 5.2 Create a Prompt

1. Choose **Create** in the workspace action button (or open `/workspace/prompts/create`). The
   **Create Prompt** dialog opens (`src/lib/components/workspace/Prompts.svelte:92-101`, `:390-406`).
2. Type a **Name**. The **Command** below it fills itself from the name (`Summarize Paper` becomes
   `summarize-paper`) until the person types in the command box. Hovering the name and command shows
   `Only alphanumeric characters and hyphens are allowed - Activate this command by typing "/{COMMAND}" to chat input.`
   (`src/lib/components/workspace/Prompts/PromptEditor.svelte:74-80`, `:572-598`).
3. Optionally add tags; suggestions come from tags on prompts the person can read (`:288-291`, `:600-611`).
4. Optionally press **Access** to share it before saving (section 5.7) (`:585-587`).
5. Type the **Prompt Content**. The box suggests `Write a summary in 50 words that summarizes {{topic}}.`
   and the hint under it reads `ⓘ Use {{variable}} for placeholders` (section 4.2) (`:616-643`).
6. Press **Save & Create**. The browser checks the command characters (section 5.3); then the server
   checks that the person has **Prompts Access** or **Import Prompts** (admins always may), drops any
   sharing entries the person may not grant, checks that no prompt anywhere uses the command, stores the
   prompt with its first version (commit message `Initial version`) and makes that version live
   (`backend/open_webui/routers/prompts.py:143-197`; `backend/open_webui/models/prompts.py:112-175`).
7. Success shows `Prompt created successfully`, closes the dialog and reloads the list
   (`src/lib/components/workspace/Prompts.svelte:249-261`). The name and content are required fields, so
   the browser's own prompt appears if either is empty.

Failures: `Only alphanumeric characters and hyphens are allowed in the command string.` (browser),
`Uh-oh! This command is already registered. Please choose another command string.` (command in use),
`401 Unauthorized` (no permission to create), `Something went wrong :/` (the database refused the save).

### 5.3 Command String Rules and "Already Registered"

| Rule | Where it is enforced | What the person sees | Source |
|---|---|---|---|
| Only letters, digits, `-` and `_` | The prompt editor, on **Save & Create**, on **Save** in **Edit Prompt** and on the automatic save of the command | `Only alphanumeric characters and hyphens are allowed in the command string.`; the automatic save also puts the last saved command back | `src/lib/components/workspace/Prompts/PromptEditor.svelte:89-124`, `:231-238` |
| Stored without a leading `/` | The browser removes it when creating; the editor removes it when loading | Commands in lists are shown with a `/` added in front | `src/lib/apis/prompts/index.ts:58-61`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:267`; `src/lib/components/workspace/Prompts.svelte:588-592` |
| Unique across the whole site | The server on create, on every content save and on the automatic save of the command; the database also has a unique index on the column | `Uh-oh! This command is already registered. Please choose another command string.` (HTTP 400) | `backend/open_webui/routers/prompts.py:177-197`, `:283-290`, `:356-363`; `backend/open_webui/models/prompts.py:29` |
| Compared exactly | The server looks the command up with an exact match | `Summarize` and `summarize` count as two different commands, although the `/` list finds both for either spelling | `backend/open_webui/models/prompts.py:190-196`; `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:77-79` |
| Disabled prompts keep their command | The look-up does not skip switched-off prompts | A disabled prompt, including one the person cannot see, still blocks its command | `backend/open_webui/models/prompts.py:190-196` |
| Deleting a prompt releases the command | The prompt row is removed | The command can be used again | `backend/open_webui/models/prompts.py:664-680` |
| Imported commands are not checked for characters | The server has no character rule | A JSON import can store a command with spaces or other characters; the editor then refuses to save that prompt's content or name until the command is changed to a valid one | `backend/open_webui/routers/prompts.py:143-197`; `src/lib/components/workspace/Prompts.svelte:424-434`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:89-124`, `:231-238` |

No length limit on the command was found in the form, the router or the column definition
(`backend/open_webui/models/prompts.py:29`, `:83-93`). Because uniqueness covers every prompt on the
site, the prompt holding a command may belong to someone else and be invisible to the person, may be
their own disabled prompt, or may belong to a deleted account (the ground truth records that deleting a
user leaves their prompts in place). Only an admin with admin bypass sees every prompt, so tier 1
escalates to find the holder (section 11.2).

### 5.4 Rename a Prompt or Change Its Command or Tags

On the prompt page the name (placeholder `Prompt Name`), the command (placeholder `command`) and the tags
are edited in place and saved automatically half a second after the last change, with the message
`Saved`. This automatic save does **not** create a version, so the version history keeps the earlier
name. If the command is invalid or already taken, an error appears and the name, command and tags all
return to their last saved values (`src/lib/components/workspace/Prompts/PromptEditor.svelte:224-261`,
`:405-462`; `backend/open_webui/routers/prompts.py:323-381`;
`backend/open_webui/models/prompts.py:558-585`). A new command takes effect at once for everyone who
uses the prompt; the old command is not kept as an alias. Read-only viewers see the fields greyed out.

### 5.5 Edit the Prompt Text (Save a New Version)

1. On the prompt page press **Edit** (shown only to the owner, people with write access and admins).
   The **Edit Prompt** dialog shows **Prompt Content**, **Commit Message** (optional, placeholder
   `Describe what changed...`) and a **Set as Production** tick box, ticked by default
   (`src/lib/components/workspace/Prompts/PromptEditor.svelte:315-389`, `:429-444`).
2. Press **Save**. The browser checks the command characters; the server checks write access, checks
   the command is not taken, filters the sharing list and saves
   (`backend/open_webui/routers/prompts.py:249-315`).
3. With **Set as Production** ticked, the prompt's text, name and tags take the new values, a new version
   is recorded and becomes live, and `Prompt updated successfully` appears. The History column reloads
   and selects the newest version (`backend/open_webui/models/prompts.py:481-556`;
   `src/routes/(app)/workspace/prompts/[id]/+page.svelte:19-40`;
   `src/lib/components/workspace/Prompts/PromptEditor.svelte:91-108`).
4. With it unticked, the prompt keeps its live text; the new text is stored only as a version that can
   be made live later (section 5.6) (`backend/open_webui/models/prompts.py:511-518`, `:549-552`).

Three side effects, read from the code (confirming them in a test environment is listed in section 14):

- **Every save creates a version, even with no change.** The editor always sends the sharing list, and
  the server treats any save that carries a sharing list as a change
  (`src/lib/components/workspace/Prompts/PromptEditor.svelte:91-100`;
  `backend/open_webui/models/prompts.py:500-506`).
- **Saving re-applies sharing with the saver's permissions.** The sharing list the editor loaded is
  filtered by the *saver's* sharing permissions and then replaces the stored one. A collaborator with
  write access but without **Prompts Public Sharing** therefore removes a **Public** setting simply by
  saving the text; people or groups are removed the same way when the saver lacks
  **Allow Sharing With Users** or **Allow Sharing With Groups** (`backend/open_webui/routers/prompts.py:292-301`;
  `backend/open_webui/utils/access_control/__init__.py:223-301`;
  `backend/open_webui/models/prompts.py:520-522`). Admins are not filtered.
- **The prompt moves to the top of the list** because its updated time changes
  (`backend/open_webui/models/prompts.py:524`).

### 5.6 Version History: View, Restore and Delete

The **History** column sits to the left of the content on medium and wide screens; on narrow screens
(phones) the prompt page shows no history list (`src/lib/components/workspace/Prompts/PromptEditor.svelte:477-483`).

| Action | How | What happens | Source |
|---|---|---|---|
| Browse | Scroll the History column | Entries newest first, 20 at a time, more loading as you scroll. Each shows the commit message (or `Update`), `Live` on the live one, the author's name and picture, and the date. `No history available` when empty | `src/lib/components/workspace/Prompts/PromptEditor.svelte:126-164`, `:677-741`; `backend/open_webui/routers/prompts.py:599-635` |
| View a version | Click an entry | Its text is shown, with the first seven characters of its id next to **Prompt Content**; the copy button copies the version on screen | `src/lib/components/workspace/Prompts/PromptEditor.svelte:166-175`, `:486-546` |
| Restore (make live) | **Set as Production** beside a non-live version | The version becomes live and the prompt takes back that version's **name, text and tags**. The **command and the sharing are not restored**. No new version is recorded. Message `Production version updated` | `src/lib/components/workspace/Prompts/PromptEditor.svelte:177-197`, `:499-512`; `backend/open_webui/routers/prompts.py:384-429`; `backend/open_webui/models/prompts.py:587-624` |
| Delete a version | **...** beside the version › **Delete**, then confirm `Delete Version` | The version is removed and versions that followed it are re-linked to the one before it. Message `Version deleted` | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:21-31`, `:63-74`; `backend/open_webui/routers/prompts.py:681-728`; `backend/open_webui/models/prompt_history.py:207-231` |
| Delete the live version | Not offered | The menu item is greyed with `Cannot delete the production version`; the server refuses with `Cannot delete the active production version` | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:54-62`; `backend/open_webui/routers/prompts.py:714-719` |

Read-only viewers can browse and copy versions but see neither **Set as Production** nor the version
menu (`src/lib/components/workspace/Prompts/PromptEditor.svelte:499`). The interface has no side-by-side
comparison of versions; the server's comparison endpoint is not called by any screen (section 14).

### 5.7 Share a Prompt

1. On the prompt page press **Access** (owners, writers and admins), or press it in **Create Prompt**
   before saving (`src/lib/components/workspace/Prompts/PromptEditor.svelte:438`, `:585-587`).
2. The share dialog, described in `users-groups-roles-and-permissions.md` (sections 5.16 and 5.17),
   offers **Public** when the person has **Prompts Public Sharing**, an access list of people and groups
   when they have **Prompts Sharing**, and **Read** or **Write** per entry
   (`src/lib/components/workspace/Prompts/PromptEditor.svelte:295-302`).
3. On an existing prompt each change is saved at once (`Saved`); in **Create Prompt** the sharing is
   saved with the prompt (`:303-312`; `backend/open_webui/routers/prompts.py:441-490`).
4. The server keeps only the entries the sharer may grant (section 3.1); the open dialog does not show
   that an entry was dropped until it is reopened.

Read access lets a person see the prompt in their `/` list and in the workspace list, open it read-only
with its history, copy it, clone it and (with **Export Prompts**) export it. Write access adds
everything the owner can do, including deleting it and changing its sharing (section 3.2). Prompts that
were public under the older storage format became **Public** grants when the database was upgraded
(section 6.5). Section 5.5 explains how a later text save by a collaborator can remove sharing.

### 5.8 Switch a Prompt Off or On

The switch at the end of each row (tooltip `Enabled` or `Disabled`) turns a prompt off or on for
everyone (`src/lib/components/workspace/Prompts.svelte:713-733`;
`backend/open_webui/routers/prompts.py:498-543`; `backend/open_webui/models/prompts.py:626-645`). A
disabled prompt disappears from every `/` list, from **Export JSON** and from tag suggestions, but stays
in the workspace list, keeps its versions and sharing, and still reserves its command (section 5.3).

The switch is drawn on every row, including `Read Only` rows. When a read-only viewer flips it, the
server refuses, no message appears, and the switch shows the wrong position until the page is reloaded
(read from code: the call has no error handling, `src/lib/components/workspace/Prompts.svelte:726-731`;
`src/lib/apis/prompts/index.ts:364-390`).

### 5.9 Clone a Prompt

Row menu › **Clone** opens **Create Prompt** filled in with the name `{name} (Clone)`, the command
`{command}-clone`, the same text, the same tags **and the same sharing list as the original**, so the
copy starts out shared with the same people unless that is changed before saving (the server still drops
entries the cloner may not grant) (`src/lib/components/workspace/Prompts.svelte:227-233`, `:263-273`;
`src/lib/components/workspace/Prompts/PromptEditor.svelte:263-275`). The version history is not copied:
the clone starts at `Initial version` and the cloner owns it. Saving needs **Prompts Access** or **Import
Prompts**. Cloning the same prompt twice fails with the "already registered" message until the second
copy's command is changed.

### 5.10 Export Prompts

| Export | Who sees it | File and content | Source |
|---|---|---|---|
| **Export JSON** (workspace action button) | Admins and people with **Export Prompts** | `prompts-export-{timestamp}.json`: every **active** prompt the person can read (for an admin with admin bypass, every active prompt on the site); disabled prompts are left out | `src/lib/components/workspace/Prompts.svelte:108-125`; `backend/open_webui/routers/prompts.py:54-61`; `backend/open_webui/models/prompts.py:200-247` |
| Row menu › **Export** | Same | `prompt-export-{timestamp}.json`: that one prompt as shown in the list | `src/lib/components/workspace/Prompts.svelte:275-280`; `src/lib/components/workspace/Prompts/PromptMenu.svelte:96-108` |

Both files hold, per prompt, the id, command, name, text, tags, on/off state, live version id and
timestamps, the sharing entries (with the ids of the people and groups shared with) and an owner record
with the owner's id, name, email address and role (`backend/open_webui/models/prompts.py:42-80`;
`backend/open_webui/models/users.py:340-348`). Treat export files as personal data. Neither export
includes version history. The server does not check **Export Prompts** (section 3.1).

### 5.11 Import Prompts

1. **Import JSON** (admins and people with **Import Prompts**) opens a file picker for a `.json` file
   (`src/lib/components/workspace/Prompts.svelte:102-107`, `:408-414`).
2. The file must contain a list of prompts. For each entry the browser creates a new prompt from its
   `command`, `name` and `content` only; tags, sharing, versions and the on/off state are **not** imported,
   the person importing becomes the owner and each prompt starts private (`:415-446`).
3. Each entry that fails shows its own red message and the import moves on to the next entry: the
   "already registered" message for a command in use (for example when the same file is imported twice),
   `401 Unauthorized` without permission, or a validation error printed as raw JSON text when an entry has
   no `name` (older Open WebUI exports used `title`, which this import does not read)
   (`src/lib/components/workspace/Prompts.svelte:424-434`; `backend/open_webui/models/prompts.py:83-93`).
4. No success message is shown; the list simply reloads (`:436-437`). A file that is not valid JSON, or
   is valid JSON but not a list, does nothing visible (read from code: the error is not caught for
   display).

### 5.12 Community Sharing and Discovery

When the admin setting **Community Sharing** (`ui.enable_community_sharing`, on in code) is on:

- The row menu shows **Share**. It displays `Redirecting you to Open WebUI Community`, opens the
  openwebui.com page for creating a prompt in a new tab and hands it the prompt **as listed, including the
  owner's name, email address and sharing entries** (`src/lib/components/workspace/Prompts/PromptMenu.svelte:70-82`;
  `src/lib/components/workspace/Prompts.svelte:206-225`; `backend/open_webui/models/prompts.py:65-70`).
- A **Discover a prompt** link (`Discover, download, and explore custom prompts`) under the list opens
  openwebui.com's prompt catalogue; a prompt sent back from that site opens pre-filled in **Create
  Prompt** (`src/lib/components/workspace/Prompts.svelte:308-333`, `:759-765`).

openwebui.com is the upstream community, not a MedIT GPT service; whether staff may use it is
**TO BE CONFIRMED** (section 14). The setting's label and description are in section 7.1. The licence
comment beside the community wordmark stays as it is (`src/lib/components/workspace/Prompts.svelte:207-209`).

### 5.13 Delete a Prompt

1. Row menu › **Delete** asks `Delete prompt?` with `This will delete {command}.`; confirming shows
   `Deleted {command}` (`src/lib/components/workspace/Prompts.svelte:292-306`, `:378-388`, `:691-694`).
2. Holding **Shift** turns each row's copy button into a bin icon; clicking it deletes the prompt
   **at once, without the confirmation**. The bin appears on read-only rows too; the server refuses those
   (`:641-655`; `backend/open_webui/routers/prompts.py:566-580`).

Deletion is permanent: the prompt, every version and every sharing entry are removed, with no recycle
bin or undo (`backend/open_webui/models/prompts.py:664-680`). Chats in which the prompt's text was
already used keep that text, because inserting a prompt copies its text into the message. Restoring a
deleted prompt needs a database backup (**TO BE CONFIRMED** whether one exists) or an earlier export
file, and re-importing a file brings back only the command, name and text (section 5.11).

### 5.14 Use a Prompt in a Chat (`/`)

1. In the message box type `/` at the start of the message or after a space. A pop-up opens with up to
   three groups, `Commands`, `Prompts` and `Skills` (section 2.2).
2. Keep typing part of the prompt's **command** (not its name). The `Prompts` group lists every prompt
   whose command contains the typed text, ignoring case, sorted by name; each row shows the command and,
   greyed, the name (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:77-85`, `:442-475`).
3. Use the arrow keys and Enter or Tab, or click. Built-in commands are listed above the prompts and Enter
   picks whichever row is highlighted, so a prompt whose command starts like `model` or `settings` may need
   an arrow press (`src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:56-83`).
4. The typed `/...` is replaced by the prompt's text. Built-in placeholders are filled in, then any
   remaining placeholders open the **Input Variables** form (section 5.15)
   (`src/lib/components/chat/MessageInput.svelte:1427-1433`, `:631-686`).
5. The text can be edited before sending; nothing is sent until the person sends it.

The `Prompts` group is fetched from the server 0.2 seconds after each keystroke, so a prompt shared or
changed a moment ago appears without reloading the page. It lists the **active** prompts the person can
read, whatever their workspace permissions; for an admin with admin bypass, every active prompt on the
site (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:93-131`;
`backend/open_webui/routers/prompts.py:54-61`). Line breaks in the prompt are kept; with the personal
setting **Insert Prompt as Rich Text** the text is inserted as formatted Markdown (section 7.3).

Two behaviours read from code (section 14): the pop-up opens only when `/` is at the start or follows a
space, which is the default of the installed TipTap suggestion library
(`node_modules/@tiptap/suggestion/src/suggestion.ts:211-214`, third-party code); and while a `/word` is
being typed, Enter is handed to the pop-up, so if nothing matches, Enter does nothing until a space is
typed (`src/lib/components/common/RichTextInput/suggestions.ts:100-105`;
`src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:71-77`;
`src/lib/components/chat/MessageInput.svelte:2138-2167`).

### 5.15 Fill In Input Variables

1. After a prompt is inserted, any `{{...}}` placeholder that is not a built-in one (or is a built-in one
   without a value, section 4.2) opens the **Input Variables** form, one field per variable, with the
   first field focused (`src/lib/components/chat/MessageInput.svelte:263-281`;
   `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:43-77`).
2. Each field is labelled with the variable name, or with its `label=` property; required fields show
   `* required` and block **Save** until filled (`:25`, `:108-117`).
3. **Save** writes the values into the message box in place of the placeholders, including identical
   placeholders already in the box and placeholders filled earlier in the same session with a value of
   the same name; Windows line endings are converted (`:27-41`;
   `src/lib/components/common/RichTextInput.svelte:581-620`;
   `src/lib/components/chat/MessageInput.svelte:275-276`).
4. **Cancel** or the X closes the form and leaves the `{{...}}` text in the message box to edit by hand;
   the form opens again only when a prompt is inserted again
   (`src/lib/components/chat/MessageInput/InputVariablesModal.svelte:370-378`).

The form appears only for text inserted by the code (the `/` list, a suggestion card or a follow-up),
not for placeholders typed or pasted by hand (`chat-composer-and-message-display.md`, section 5.8). A
placeholder whose name contains a space, `|` or `}` is not recognized and stays as plain text
(`src/lib/utils/index.ts:1731-1751`). Values typed into the form become part of the message and of the
saved chat.

### 5.16 Find and Browse Skills

1. Open **Workspace › Skills** (`/workspace/skills`). The page needs **Skills Access** or the admin role
   (section 3.1).
2. The list shows 30 skills per page, most recently changed first. Each row shows the skill's name (in
   the person's interface language when a translation exists; hover shows the id), the id after a `/`,
   how long ago it changed (hover for the full date), an `Inactive` badge when it is switched off, a
   `Read Only` badge when the person cannot change it, the description, and the owner's name on wider
   screens (hover shows the owner's email; `Deleted User` when the account no longer exists). The
   **...** menu and the on/off switch appear only on rows the person can change
   (`src/lib/components/workspace/Skills.svelte:432-597`, `:601-605`).
3. **Search Skills** filters after a 0.3-second pause; it matches the name, description and id, and the
   owner's name and email (`src/lib/components/workspace/Skills.svelte:136-146`;
   `backend/open_webui/models/skills.py:233-243`). There is no tag filter for skills.
4. The view filter (`All`, `Created by you`, `Shared with you`) is shared with the other workspace
   sections. **Title** and **Updated at** sort the list; a second click reverses the order. Sorting by
   title uses the default-language name (`src/lib/components/workspace/Skills.svelte:159-166`,
   `:376-384`, `:398-428`; `backend/open_webui/models/skills.py:264-268`).
5. Inactive skills stay in the list. Nothing matching shows `No skills found` with
   `Try adjusting your search or filter to find what you are looking for.` (`:606-615`).
6. Clicking a row opens `/workspace/skills/edit?id={id}` (`:168-170`).

### 5.17 Create a Skill

1. Choose **Create** in the workspace action button (admins and people with **Skills Access**); it opens
   `/workspace/skills/create` (`src/lib/components/workspace/Skills.svelte:75-80`).
2. Type the **Skill Name** (tooltip `e.g. Code Review Guidelines`). On a new skill the **Skill ID** under
   it follows the name: accents removed, spaces become hyphens, other characters dropped, lower case
   (tooltip `e.g. code-review-guidelines`). The ID is recalculated whenever the name changes, so an ID
   typed by hand is overwritten if the name is edited afterwards. A name made only of other characters
   (for example emoji or a non-Latin script) gives an empty ID, which must then be typed
   (`src/lib/components/workspace/Skills/SkillEditor.svelte:37-39`, `:128-161`;
   `src/lib/utils/index.ts:1699-1713`).
3. Optionally type a **Skill Description** (tooltip `e.g. Step-by-step instructions for code reviews`).
   In native mode the model sees only the name and description until it loads the skill, so a specific
   description helps it choose (section 5.26) (`src/lib/components/workspace/Skills/SkillEditor.svelte:163-177`;
   `backend/open_webui/utils/middleware.py:2849-2854`).
4. Type the instructions in Markdown in the large box (placeholder `Enter skill instructions in markdown...`).
   If the text begins with a front-matter block (`---` lines holding `name:` and `description:`), empty
   name and description fields are filled from it; the front matter stays in the instructions
   (`src/lib/components/workspace/Skills/SkillEditor.svelte:41-50`, `:193-208`;
   `src/lib/utils/index.ts:2448-2468`).
5. Optionally pick a language in the **Editing language** selector (first choice `Default`) to type a
   translated name and description; languages that have a translation are marked with ` *`.
   Translations are shown to people using that interface language; the model always receives the
   default-language name and description (`src/lib/components/common/LanguageModeSelect.svelte:21-38`;
   `src/lib/components/common/LocalizedField.svelte:16-30`; `backend/open_webui/utils/middleware.py:2843-2854`).
6. Optionally press **Access** to share it before saving (section 5.20).
7. Press **Save & Create**. The browser requires the name, ID and instructions; if the default-language
   name is blank while a translation is being edited, the editor silently switches back to `Default`
   (`src/lib/components/workspace/Skills/SkillEditor.svelte:52-78`, `:211-223`). The server then:
   - checks **Skills Access** or **Import Skills** (admins always pass), otherwise `401 Unauthorized`;
   - lower-cases the ID and turns spaces into hyphens, then refuses anything other than `a-z`, `0-9`, `-`
     and `_` with `[ERROR: Invalid skill ID]`;
   - refuses an ID that any skill already has with
     `Uh-oh! This id is already registered. Please choose another id string.`;
   - drops sharing entries the person may not grant;
   - stores the skill as active. A name that another skill already has makes the database refuse the
     save, shown as `[ERROR: Error creating skill]` (`backend/open_webui/routers/skills.py:151-219`;
     `backend/open_webui/models/skills.py:20-32`, `:123-148`).
8. Success shows `Skill created successfully`, refreshes the browser's list of skills and returns to
   `/workspace/skills` (`src/routes/(app)/workspace/skills/create/+page.svelte:23-34`).

Both the ID and the name are unique across the whole site, including skills the person cannot see, and
the ID cannot be changed later (section 5.19).

### 5.18 Import Skills (JSON or Markdown)

**Import JSON** in the workspace action button (admins and people with **Import Skills**) opens a file
picker that accepts `.json` and `.md` files (`src/lib/components/workspace/Skills.svelte:81-86`,
`:268-273`). Despite the label, the two kinds of file behave differently:

| File | What happens | Source |
|---|---|---|
| `.json` | Read as one skill or a list of skills. Each entry is sent to the server as it is, so its id, name, description, instructions, translations, on/off state **and sharing entries** come from the file; the server applies the checks of section 5.17 and drops sharing entries the importer may not grant. The importer becomes the owner. Each failing entry shows its own red message, and then `Skill imported successfully` appears **even if every entry failed**. A file that is not valid JSON shows `Invalid JSON file` | `src/lib/components/workspace/Skills.svelte:279-304`; `backend/open_webui/routers/skills.py:151-219`; `backend/open_webui/models/skills.py:87-94` |
| `.md` | Nothing is saved yet: the editor opens on `/workspace/skills/create`, filled in. The name comes from the front matter's `name:` (or the file name) with hyphens and underscores turned into spaces and each word capitalized; the ID from the same text as a slug; the description from `description:`; the instructions are the whole file, front matter included. The ID no longer follows name changes. Press **Save & Create** to keep it | `src/lib/components/workspace/Skills.svelte:305-327`; `src/routes/(app)/workspace/skills/create/+page.svelte:36-52`; `src/lib/components/workspace/Skills/SkillEditor.svelte:37-39`; `src/lib/utils/index.ts:2448-2468` |

Read from code: an entry without `id`, `name` or `content` fails the server's form check, and its message
appears as `[object Object]` because the browser prints the list of form errors as text
(`src/lib/apis/skills/index.ts:21-29`; `src/lib/components/workspace/Skills.svelte:291-293`).
Importing the same file twice fails for every entry with the "id is already registered" message. A JSON
file exported from another Open WebUI instance can carry sharing entries naming people and groups that
do not exist here; they are stored but grant nothing.

### 5.19 Edit a Skill or Read a Shared One

1. Click a row, or **...** › **Edit**, to open `/workspace/skills/edit?id={id}`
   (`src/lib/components/workspace/Skills.svelte:168-170`, `:540-571`;
   `src/lib/components/workspace/Skills/SkillMenu.svelte:42-65`). When the skill cannot be loaded, the
   server's message appears and the list returns: `We could not find what you're looking for :/` when it
   no longer exists, `You do not have permission to access this resource. Please contact your administrator for assistance.`
   when the person cannot read it (`src/routes/(app)/workspace/skills/edit/+page.svelte:42-66`;
   `backend/open_webui/routers/skills.py:227-266`).
2. People without write access see a `Read Only` badge, the instructions as plain text and no **Save**
   button (`src/lib/components/workspace/Skills/SkillEditor.svelte:183-198`, `:211-224`).
3. Owners, people with write access and admins can change the name, description, translations and
   instructions; the ID is shown but cannot be edited (`:140-161`). **Save** sends everything; the server
   checks write access (`401 Unauthorized` otherwise), drops sharing entries the saver may not grant and
   overwrites the skill. A name that another skill already has gives `[ERROR: Error updating skill]`
   (`backend/open_webui/routers/skills.py:274-345`; `backend/open_webui/models/skills.py:317-332`).
4. Success shows `Skill updated successfully` (`src/routes/(app)/workspace/skills/edit/+page.svelte:19-40`).

Skills keep no history: a save replaces the previous instructions for good, and the next message in any
chat that uses the skill gets the new text. Read from code, a save has two side effects like those of a
prompt save (section 5.5): it re-applies the sharing list with the saver's permissions, so a
collaborator without **Skills Public Sharing** removes **Public** simply by saving; and it writes back the
on/off state the editor loaded, so saving a page that was opened before someone switched the skill off
switches it on again (`src/lib/components/workspace/Skills/SkillEditor.svelte:65-74`;
`backend/open_webui/routers/skills.py:310-323`; `backend/open_webui/models/skills.py:322-326`).

### 5.20 Share a Skill

1. Press **Access** in the skill editor (owners, people with write access and admins; on a new skill,
   before saving) (`src/lib/components/workspace/Skills/SkillEditor.svelte:181-190`).
2. The share dialog is the one described in `users-groups-roles-and-permissions.md` (sections 5.16 and
   5.17): **Public** needs **Skills Public Sharing**, the access list of people and groups needs
   **Skills Sharing**, and each entry gets **Read** or **Write** (`:93-100`).
3. On an existing skill each change is saved at once with `Saved`; on a new skill the sharing is saved
   with it (`:101-110`; `backend/open_webui/routers/skills.py:357-406`). The server keeps only the
   entries the sharer may grant (section 3.1).

**Read** lets a person use the skill in chats and open it read-only; **Write** adds editing, sharing,
switching it off and deleting it (section 3.2). Sharing also decides who benefits when the skill is a
model's default (section 5.24).

### 5.21 Switch a Skill Off or On

The switch at the end of a row (tooltip `Enabled` or `Disabled`), shown only to people who can change the
skill, turns it off or on for everyone (`src/lib/components/workspace/Skills.svelte:573-591`;
`backend/open_webui/routers/skills.py:414-459`). An inactive skill keeps its row (badge `Inactive`) and
its sharing, but:

- the server leaves it out of every chat, and `view_skill` answers `Skill '{id}' not found`
  (`backend/open_webui/utils/middleware.py:2836-2839`; `backend/open_webui/tools/builtin.py:3518-3521`);
- the Integrations menu, the model defaults and the model editor's picker hide it
  (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:167-175`;
  `src/lib/components/chat/Chat.svelte:1062-1073`; `src/lib/components/workspace/Models/SkillsSelector.svelte:20-21`);
- the `$` and `/` lists still offer it; picking it inserts a chip that does nothing for the model, and the
  chip's text stays in the message as typed (`src/lib/components/chat/MessageInput/Commands/Skills.svelte:41-47`;
  `backend/open_webui/utils/middleware.py:2907-2909`).

The browser ignores the server's answer to the switch, so a refused change (for example after write
access was taken away) shows no message and the switch shows the wrong position until the page is
reloaded (read from code, `src/lib/components/workspace/Skills.svelte:584-589`).

### 5.22 Clone or Export a Skill

| Action | Who sees it | What happens | Source |
|---|---|---|---|
| **...** › **Clone** | People who can change the skill (the menu is hidden on `Read Only` rows) | Opens the create page filled in with the ID `{id}_clone`, the name `{name} (Clone)` and the same description, instructions, translations and on/off state, **and the same sharing list**. The ID does not follow name changes. Saving needs **Skills Access** or **Import Skills**; a second clone of the same skill fails with the "id is already registered" message until its ID is changed | `src/lib/components/workspace/Skills.svelte:176-190`, `:521`; `src/routes/(app)/workspace/skills/create/+page.svelte:36-52` |
| **...** › **Export** | Admins and people with **Export Skills**, on rows they can change | `skill-{id}-export-{timestamp}.json`: a list holding that one skill | `src/lib/components/workspace/Skills/SkillMenu.svelte:78-89`; `src/lib/components/workspace/Skills.svelte:192-204` |
| **Export JSON** (workspace action button) | Admins and people with **Export Skills**; the server refuses anyone else with `401 Unauthorized` | `skills-export-{timestamp}.json`: every skill the person can read, active or not (for an admin with admin bypass, every skill on the site) | `src/lib/components/workspace/Skills.svelte:87-103`; `backend/open_webui/routers/skills.py:123-143` |

Export files hold, per skill, the id, the owner's user id, name, description, instructions, translations,
on/off state, timestamps and sharing entries (with the ids of the people and groups shared with). Unlike
prompt exports they carry no owner name or email (`backend/open_webui/models/skills.py:40-53`,
`:65-84`; `backend/open_webui/routers/skills.py:123`, `:227-256`). Treat them as internal data; importing
one brings its sharing entries back (section 5.18).

### 5.23 Delete a Skill

1. **...** › **Delete** asks `Delete skill?` with `This will delete {name}.`; confirming shows
   `Skill deleted successfully` (`src/lib/components/workspace/Skills.svelte:206-219`, `:618-629`).
2. Holding **Shift** turns the menu button into a bin icon that deletes the skill **at once, without the
   confirmation** (only on rows the person can change) (`:523-537`).

The server lets the owner, people with write access and admins delete (`401 Unauthorized` otherwise); it
removes every sharing entry and the row. There is no recycle bin, history or undo
(`backend/open_webui/routers/skills.py:467-506`; `backend/open_webui/models/skills.py:350-359`). The ID
and the name become free again. Models that list the skill as a default keep the stale id, which the
server skips; past chats keep their text, and an old `$` mention of the skill no longer loads anything
(`backend/open_webui/utils/middleware.py:2833-2839`). Restoring a deleted skill needs a database backup
(**TO BE CONFIRMED** whether one exists) or an earlier export file.

### 5.24 Attach Skills to a Model

Model owners attach skills in the model editor (Workspace › Models › edit) under **Skills**: **Select
Skill** opens a searchable list (`Search skills`) of the active skills the editor can read; chosen skills
appear as ticked names, **Disable all** clears them, and the note under them reads
`To select skills here, add them to the "Skills" workspace first.` The choice is saved as the model's
`meta.skillIds` (`src/lib/components/workspace/Models/SkillsSelector.svelte:20-99`;
`src/lib/components/workspace/Models/ModelEditor.svelte:353-358`, `:483`, `:1203`). The editor itself is
described in `workspace-models-and-model-access.md` (section 5.5).

What the attachment does, read from code:

- When a new chat starts with that model alone, its default skills that are active and readable by the
  person are switched on in the Integrations menu (`src/lib/components/chat/Chat.svelte:1062-1073`).
- The server **also adds the model's default skills to every request by itself**, whatever the menu shows
  (`backend/open_webui/utils/middleware.py:2772-2776`). Switching a default skill off in the
  Integrations menu therefore does not remove it: with built-in tools off its full instructions are still
  sent, and with built-in tools on it stays in the model's list (section 5.26). Confirming this in a test
  environment is listed in section 14.
- Default skills are looked up with the **chatting person's** access, so a colleague using a shared model
  gets only the default skills that are also shared with them (`backend/open_webui/utils/middleware.py:2830-2839`;
  `workspace-models-and-model-access.md`, section 11.8).

### 5.25 Use Skills in a Chat

| Way | How | What happens to the skill | Source |
|---|---|---|---|
| **Integrations** menu › **Skills** | The menu shows **Skills** with a count when at least one active skill or terminal skill is available; the sub-list (`Search skills`, `No skills found`) has a switch per skill, terminal skills labelled `Terminal` | Switched-on skills are sent as `skill_ids` with every message in the chat, and kept in the browser tab's saved draft of the message box | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:167-189`, `:216-228`, `:337-358`, `:655-731`; `src/lib/components/chat/Chat.svelte:3568-3593`, `:4037-4070` |
| Model default | Section 5.24 | Added by the server on every message | `backend/open_webui/utils/middleware.py:2772-2776` |
| `$` mention | Type `$` and part of a skill's name, description, id or owner's name; pick one. A chip such as `$Code Review Guidelines` appears | The skill's full instructions are given to the model; because earlier messages are scanned too, they are given again on every later message of the chat | `src/lib/components/chat/MessageInput/Commands/Skills.svelte:41-62`; `src/lib/components/chat/MessageInput.svelte:1554-1564`; `backend/open_webui/utils/skills.py:23-29`; `backend/open_webui/utils/middleware.py:2770-2776`, `:2841-2848` |
| `/` list › **Skills** | The same skills as the `$` list, below the prompts | Read from code, the pick is inserted as an `@`-marked chip (`<@{id}\|{name}>`) that the server does not match, so the skill is **not** loaded the way a `$` mention is; with built-in tools on it is still in the model's list like any other readable skill | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:119-131`, `:477-518`; `src/lib/components/chat/MessageInput.svelte:1427-1460`; `backend/open_webui/utils/skills.py:8-10` |

The `/` behaviour comes from the chat composer's own `/` handler, which inserts the chip without saying
which character triggered it, so the editor library's default marker `@` applies (third-party TipTap code,
`node_modules/@tiptap/extension-mention/src/mention.ts:216-224`); the `$` list uses the library's default
handler, which records `$`. Advise people to use `$` or the Integrations switch. Confirming this in a test
environment is listed in section 14.

- **The skills chip.** When at least one skill is switched on, a cube icon with the count appears under the
  message box (tooltip `{COUNT} Available Skills`); clicking it opens **Available Skills**, listing the
  name and description of each switched-on skill (`src/lib/components/chat/MessageInput.svelte:2390-2412`;
  `src/lib/components/chat/SkillsModal.svelte:22-66`). `$` mentions are not counted.
- **Lists can be out of date.** The Integrations menu reads the person's skills once per page load (and
  again after they change skills in the workspace in the same tab), so a skill shared a moment ago
  appears after a reload. The `$` and `/` lists ask the server again after each keystroke but show only
  the first 30 matching skills, most recently changed first, inactive ones included
  (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:216-228`;
  `src/lib/components/chat/Chat.svelte:1019-1021`; `src/lib/components/chat/MessageInput/Commands/Skills.svelte:30-47`;
  `backend/open_webui/routers/skills.py:63-115`).
- **Terminal skills** come from the terminal selected in the chat; they appear in all three lists labelled
  `Terminal`, and choosing another terminal clears them from the selection
  (`src/lib/components/chat/Chat.svelte:1000-1005`; `src/lib/apis/terminal/index.ts:345-366`).

### 5.26 How a Model Reads a Skill

The server decides, for each message, how skills reach the model
(`backend/open_webui/utils/middleware.py:2770-2921`).

**Which skills.** It gathers the switched-on skills, the model's default skills and every skill mentioned
with `$` anywhere in the conversation, then keeps those that are **active and readable by the person**
(owned, shared with them or one of their groups, or public). Admin bypass does not apply on this path
(`:2770-2776`, `:2826-2839`; `backend/open_webui/models/skills.py:167-188`).

**Two delivery modes.**

| Mode | When | What the model gets | Source |
|---|---|---|---|
| Built-in tools on (native) | The request comes from the app (it carries a session), **Function Calling** is not `Legacy`, and the model's **Builtin Tools** capability is on; also every note's AI chat | Every active skill the person can read, not only the gathered ones. Skills mentioned with `$` arrive in full as `<skill name="{name}">` … `</skill>` in the system message; all others are listed inside `<available_skills>` with their id, name and description, and the `view_skill` tool is offered so the model can load one | `:2809-2813`, `:2830-2832`, `:2841-2854`, `:2900-2905`; `backend/open_webui/utils/tools.py:734-736` |
| Built-in tools off | **Function Calling** is `Legacy`, the **Builtin Tools** capability is off, or the request came through the API | Only the gathered skills, each in full in the system message, on every message | `:2833-2848` |

How the session, Function Calling and the capability are decided is described in
`builtin-native-tools.md` (sections 3.1 and 7.4).

**Loading on demand.** In native mode the model decides whether to call `view_skill` with an id from the
list; nothing forces it to. The call returns the skill's name and instructions, or `Skill '{id}' not found`
(unknown or inactive) or `Access denied` (section 10.6); an admin can load any active skill by id
(`backend/open_webui/tools/builtin.py:3482-3545`). The call shows in the reply like any tool call, with
`View Result from view_skill` once it has finished, unless the person has **Hide Processing Details** on
(section 12; `src/lib/components/common/ToolCallDisplay.svelte:243-253`; `builtin-native-tools.md`,
section 5.6).

**Tidying the message.** Each resolved `$` mention is replaced by the skill's name before the model sees
the text; a message that held only mentions becomes the list of skill names, unless files are attached.
Mentions that were not resolved (inactive, unreadable or unknown skills, and `/` picks) stay as typed
(`backend/open_webui/utils/middleware.py:2907-2921`; `backend/open_webui/utils/skills.py:170-187`).

**What is not done** (read from code). Placeholders such as `{{USER_NAME}}` inside a skill are not
filled in, because skills are added after the system prompt's placeholders have been processed
(`backend/open_webui/utils/middleware.py:2532`, `:2592`, `:2841-2848`); translations are not sent; and
there is no size limit, so long instructions take up the model's context on every message when built-in
tools are off.

**Terminal skills** are listed from the selected terminal and loaded through it in the same two ways
(`backend/open_webui/utils/middleware.py:2856-2898`; `backend/open_webui/utils/terminals.py:247-308`); the
terminal connection itself is described in `workspace-tools-tool-servers-mcp-and-terminals.md`.

### 5.27 Create a Terminal Skill (`/skills:create`)

1. With a terminal selected in the chat and some content already in it, typing `/` offers **Create skill**
   (`/skills:create`, tooltip `Create a reusable terminal skill from this chat.`); choosing it sends
   `/skills:create` at once (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:72-74`,
   `:383-411`; `src/lib/components/chat/MessageInput.svelte:588-592`, `:1434-1446`). Typing
   `/skills:create` followed by a request and sending it works the same way.
2. The server replaces that message with authoring instructions for the model: gather the sources the
   person named, write one `SKILL.md` following the built-in authoring standards, save it on the terminal
   under `.agents/skills/<skill-name>/SKILL.md`, and report the skill's name, location and a one-line
   summary (`backend/open_webui/utils/skills.py:35-115`, `:147-167`; `backend/open_webui/utils/middleware.py:2753-2764`).
3. Without a selected terminal, or when the chat has no earlier content, the model is told instead to
   explain that skill creation needs a selected Open Terminal, or an existing chat with the workflow in it
   (`backend/open_webui/utils/skills.py:118-144`).

The result is a **terminal** skill stored on the terminal, not a workspace skill: it does not appear under
Workspace › Skills. Whether the file is written depends on the model and the terminal's tools.

## 6. Data Model

Prompts and skills have three tables of their own (`prompt`, `prompt_history`, `skill`) and share the
`access_grant` table with the other workspace items. None of these tables declares a foreign key, so
nothing is removed automatically when an owner, a person shared with or a group disappears. Timestamps
are whole seconds since 1970 (epoch). Live row counts are data and **TO BE CONFIRMED** (section 14).

### 6.1 The `prompt` Table

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | A random UUID made at creation; it is the last part of the prompt page's address and can be copied there (`Click to copy ID`) | `backend/open_webui/models/prompts.py:28`, `:116`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:464-474` |
| `command` | text, unique, indexed | The slash command without the `/`; unique across the site and compared exactly (section 5.3) | `backend/open_webui/models/prompts.py:29` |
| `user_id` | text, indexed | The owner's user id | `:30` |
| `name` | text | The display name | `:31` |
| `content` | text | The live prompt text | `:32` |
| `data`, `meta` | JSON | Set to `{}` at creation; no screen in this release writes them, but versions copy them | `:33-34`, `:126-127` |
| `tags` | JSON list | Free-text tags | `:35` |
| `is_active` | boolean | The on/off switch; new prompts are on | `:36`, `:129` |
| `version_id` | text | The id of the live row in `prompt_history` | `:37`, `:168-170` |
| `created_at`, `updated_at` | integer | `updated_at` changes on every content save, name/command/tag save, version restore and on/off switch, which is why the list's default order moves | `:38-39`, `:524`, `:580`, `:618`, `:640` |

The migration that built this table made `user_id`, `name`, `content`, `created_at` and `updated_at`
required and gave `is_active` a database default of true
(`backend/open_webui/migrations/versions/374d2f66af06_add_prompt_history_table.py:65-80`).

### 6.2 The `prompt_history` Table (Versions)

| Column | Meaning | Source |
|---|---|---|
| `id` | UUID of the version; its first seven characters are shown beside **Prompt Content** when the version is selected | `backend/open_webui/models/prompt_history.py:22`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:492-496` |
| `prompt_id` | The prompt it belongs to (indexed) | `backend/open_webui/models/prompt_history.py:23` |
| `parent_id` | The version it was saved after: the **newest** version at the time of the save, which is not necessarily the live one | `:24`; `backend/open_webui/models/prompts.py:495-496`; `backend/open_webui/models/prompt_history.py:118-134` |
| `snapshot` | A JSON copy of `name`, `content`, `command`, `data`, `meta`, `tags` and `access_grants` (each sharing entry with its id, the resource, principal type and id, permission and time) | `backend/open_webui/models/prompt_history.py:25`; `backend/open_webui/models/prompts.py:146-156`, `:530-538` |
| `user_id` | Who saved it; shown as the author in the History column | `backend/open_webui/models/prompt_history.py:26` |
| `commit_message` | The optional note (`Initial version` for the first one when none is typed) | `:27`; `backend/open_webui/models/prompts.py:163` |
| `created_at` | When it was saved; History is ordered by it, newest first | `backend/open_webui/models/prompt_history.py:28`, `:74-91` |

- A version is written by creating a prompt and by every content save (section 5.5); saving only the name,
  command or tags, restoring a version and switching the prompt off write none
  (`backend/open_webui/models/prompts.py:112-175`, `:481-556`, `:558-645`).
- Deleting a version removes that row and points its children at its own parent; the live version cannot
  be deleted through the interface or the server (`backend/open_webui/models/prompt_history.py:207-231`;
  `backend/open_webui/routers/prompts.py:714-719`).
- Versions of prompts converted from the older storage format hold `access_control` instead of
  `access_grants`, have no `tags` and no commit message (shown as `Update`)
  (`backend/open_webui/migrations/versions/374d2f66af06_add_prompt_history_table.py:156-174`).
- The version list the browser receives includes each author's id, name, role and email address,
  although the History column shows only the name and picture
  (`backend/open_webui/models/prompt_history.py:74-103`; `backend/open_webui/models/users.py:340-348`).
  Anyone who can read a prompt therefore receives the email addresses of everyone who saved a version of
  it; treat screenshots of browser developer tools accordingly.

### 6.3 The `skill` Table

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | The skill ID (a lower-case slug) chosen at creation; permanent | `backend/open_webui/models/skills.py:23`; `backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_skill_table.py:27` |
| `user_id` | text, required, indexed (`idx_skill_user_id`) | The owner's user id | `backend/open_webui/models/skills.py:24`; migration `:28`, `:37` |
| `name` | text, required, unique | The default-language display name | `backend/open_webui/models/skills.py:25`; migration `:29` |
| `description` | text, optional | The one-line description given to the model | `backend/open_webui/models/skills.py:26` |
| `content` | text, required | The Markdown instructions | `:27`; migration `:31` |
| `meta` | JSON | `i18n` (per language code, a translated `name` and `description`) and `tags` (no screen uses it) | `backend/open_webui/models/skills.py:28`, `:35-37` |
| `is_active` | boolean, required | The on/off switch | `:29`; migration `:33` |
| `updated_at`, `created_at` | integer, required; `updated_at` indexed (`idx_skill_updated_at`) | `updated_at` changes on every save and switch | `backend/open_webui/models/skills.py:31-32`, `:323`, `:343`; migration `:34-38` |

Skills keep no versions: a save overwrites the row (`backend/open_webui/models/skills.py:317-332`).

### 6.4 Sharing Rows in `access_grant`

Sharing for both is stored as rows in `access_grant` with `resource_type` `prompt` or `skill` and
`resource_id` set to the prompt's UUID or the skill ID; the table and its meaning (Public, named people,
groups, Read and Write) are described in `users-groups-roles-and-permissions.md` (section 6.3)
(`backend/open_webui/models/access_grants.py:25-45`).

- Every change of sharing, and every content save of a prompt or save of a skill, **replaces all rows**
  for that item with the filtered list (`backend/open_webui/models/access_grants.py:443-478`;
  `backend/open_webui/models/prompts.py:520-522`; `backend/open_webui/models/skills.py:322-326`).
- Owners need no row. **Write** is stored as a read row plus a write row; lists look only at read rows
  and edits only at write rows (`backend/open_webui/models/access_grants.py:562-620`, `:723-830`).
- `anyone` rows (open link sharing) are always stripped for prompts and skills (section 3.1).
- No admin screen lists these rows; the item's **Access** dialog is the only view of them.

### 6.5 Migrations That Shaped These Tables

| Revision | Date in the file | What it did in this area | Source |
|---|---|---|---|
| `7e5b5dc7342b` (initial schema) | none | Created the first `prompt` table, keyed by `command`, with `user_id`, `title`, `content` and `timestamp` | `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:120-130` |
| `922e7a387820` | 2024-11-14 | Added an `access_control` JSON column to `prompt` (empty for existing rows) | `backend/open_webui/migrations/versions/922e7a387820_add_group_table.py:5`, `:53-56` |
| `374d2f66af06` | 2026-01-23 | Rebuilt `prompt` through the temporary table `prompt_new` with a UUID `id`, `name` taken from `title`, `data`, `meta`, `tags`, `is_active`, `version_id` and `created_at`/`updated_at` taken from `timestamp`; removed a leading `/` from commands; created `prompt_history` with one first version per existing prompt | `backend/open_webui/migrations/versions/374d2f66af06_add_prompt_history_table.py:21-183` |
| `f1e2d3c4b5a6` | 2026-02-05 | Created `access_grant` and converted each prompt's `access_control`: an empty (null) value became a **Public** read row, `{}` stayed private, listed people and groups became rows; then dropped the column | `backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py:28-223` |
| `a1b2c3d4e5f6` | 2026-02-11 | Created `skill` with its two indexes | `backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_skill_table.py:21-38` |
| `461111b60977` | 2026-05-14 | Made `id` the primary key of `prompt` on older databases where it was only unique | `backend/open_webui/migrations/versions/461111b60977_add_missing_primary_keys_to_legacy_.py:20-37` |

Because of the `f1e2d3c4b5a6` rule, a prompt saved before sharing existed (no `access_control` value)
became visible to every signed-in user when the database was upgraded. Which prompts on the production
database are Public for that reason is data and **TO BE CONFIRMED**.

### 6.6 Where Else Prompt and Skill Data Lives

| Place | What is kept | Source |
|---|---|---|
| Chats | The text of a used prompt, with its placeholders already filled in, is part of the person's message; a `$` mention stays in the saved message as `<$id\|name>`. Both travel with the chat into shares and exports | `src/lib/components/chat/MessageInput.svelte:631-686`; `backend/open_webui/utils/skills.py:8-10` |
| Models | Default skills as `meta.skillIds` | `src/lib/components/workspace/Models/ModelEditor.svelte:353-358` |
| A reply waiting for tool approval | `skill_ids` with the rest of the request, so the reply can resume | `backend/open_webui/utils/middleware.py:3634-3655` |
| The browser | The tab's draft of the message box (`chat-input` or `chat-input-{chat id}` in session storage) with the switched-on skill ids; `sessionStorage.skill` carrying a clone or Markdown import to the create page (`sessionStorage.prompt` is read in the same way, but nothing in this release writes it); the workspace view filter in `localStorage.workspaceViewOption` | `src/lib/components/chat/Chat.svelte:4032-4070`; `src/lib/components/workspace/Skills.svelte:183-188`, `:315-322`; `src/lib/components/workspace/Prompts.svelte:309`, `:326-329`, `:495` |
| Export files | Sections 5.10 and 5.22 | as cited there |
| Event payloads | Section 9 | `backend/open_webui/events.py:519-554` |

**Placeholders that insert personal data.** `{{USER_NAME}}`, `{{USER_EMAIL}}`, `{{USER_LOCATION}}`,
`{{USER_BIO}}`, `{{USER_GENDER}}`, `{{USER_BIRTH_DATE}}` and `{{USER_AGE}}` insert the name, email
address, browser location (latitude and longitude), bio, gender, date of birth and age of the person
**using** the prompt, and `{{CLIPBOARD}}` inserts whatever they had copied (section 4.2). The values are
filled in that person's browser and end up in that person's chat, not in the `prompt` table; a prompt
shared by someone else never reveals the author's details this way. Skills have no placeholders:
`{{...}}` text in a skill reaches the model unchanged (section 5.26).

### 6.7 Deletion and Retention

| Event | What is removed | What stays | Source |
|---|---|---|---|
| A prompt is deleted | The row, every version and every sharing row | Chats that used it; the command becomes free | `backend/open_webui/models/prompts.py:664-680` |
| A version is deleted | That version | Its children, re-linked to its parent | `backend/open_webui/models/prompt_history.py:207-231` |
| A skill is deleted | The row and every sharing row | Chats; stale ids in models' `meta.skillIds`; the ID and name become free | `backend/open_webui/models/skills.py:350-359` |
| A user account is deleted | Not their prompts, versions or skills | Their prompts and skills stay, shown with the owner `Deleted User`; their commands, skill IDs and skill names stay reserved; sharing rows naming them stay | `knowledgebase/tools/ground-truth.md` (Accounts and Access); `src/lib/components/workspace/Prompts.svelte:627-637`; `src/lib/components/workspace/Skills.svelte:508-518` |

There is no retention period, archive or automatic clean-up for any of these tables (section 8). After an
owner's account is deleted, only admins (who find the items in the lists when admin bypass is on) and
people the items were shared with for writing can still change or delete them (section 3.2).

## 7. Settings and Configuration

Live values of every setting below are data held in the `config` table or the environment and are
**TO BE CONFIRMED** for production; the values given are the code defaults
(`knowledgebase/tools/ground-truth.md`, Settings: Where a Value Comes From).

### 7.1 Persistent Settings (Admin Panel)

| Key in the `config` table | Where admins change it | Code default (seeded from) | Effect in this area | Source |
|---|---|---|---|---|
| `user.permissions`: `workspace.prompts`, `workspace.prompts_import`, `workspace.prompts_export`, `workspace.skills`, `workspace.skills_import`, `workspace.skills_export`, `sharing.prompts`, `sharing.public_prompts`, `sharing.skills`, `sharing.public_skills`, `access_grants.allow_users`, `access_grants.allow_groups` | Admin Panel › Users › Groups: the default permissions and each group's permissions | The ten prompt and skill keys off; the two `access_grants` keys on (the `USER_PERMISSIONS_*` variables in section 7.2) | Who may open the sections, create, import, export and share (section 3.1) | `backend/open_webui/config.py:1741-1824`, `:1841-1846`, `:1940-1975`; `src/lib/components/admin/Users/Groups/Permissions.svelte:103-228`, `:313-420` |
| `ui.enable_community_sharing` | Admin Settings › General › **Community Sharing**, described as `Allow users to share chats with the Open WebUI community.` | on (`ENABLE_COMMUNITY_SHARING`) | Also shows the prompt menu's **Share** and the **Discover a prompt** link (section 5.12), although the description mentions only chats | `backend/open_webui/config.py:2096`, `:3123`; `src/lib/components/admin/Settings/General.svelte:276-283`; `src/lib/i18n/locales/en-US/translation.json:2378-2379`; `backend/open_webui/main.py:2369`; `src/lib/components/workspace/Prompts.svelte:759-765`; `src/lib/components/workspace/Prompts/PromptMenu.svelte:70-82` |
| `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | Admin Settings › Models › model defaults › **Prompt Suggestions** | `DEFAULT_PROMPT_SUGGESTIONS` (unset means the interface's built-in suggestions; an empty list turns them off) and `{}` | The new-chat suggestion cards, which are not workspace prompts (section 4.3) | `backend/open_webui/config.py:1678-1685`, `:3091-3092`; `backend/open_webui/routers/configs.py:806-840`; `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:261`; `src/lib/i18n/locales/en-US/translation.json:2608` |
| `events.webhooks` | Admin Settings › General › **Webhooks** (`Send product events as JSON to external services. Chat destinations receive readable messages.`) | none | Which outside services receive the prompt and skill events of section 9 | `backend/open_webui/events.py:20`, `:838-852`; `src/lib/components/admin/Settings/General.svelte:418`; `src/lib/i18n/locales/en-US/translation.json:2381-2382` |

There is no admin setting that turns prompts or skills off as a whole: the permissions decide who sees
the workspace sections, and anyone signed in can still use what is shared with them (section 3.1).

### 7.2 Environment-Only Settings

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `BYPASS_ADMIN_ACCESS_CONTROL` (falls back to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) | `True` | Admins see and may change every prompt and skill in the workspace lists, the `/` list and exports (section 3.2); it does not affect which skills reach an admin's chats | `backend/open_webui/config.py:2084-2092` |
| `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS`, `..._PROMPTS_IMPORT`, `..._PROMPTS_EXPORT`, `..._PROMPTS_ALLOW_SHARING`, `..._PROMPTS_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_SKILLS_ACCESS`, `..._SKILLS_IMPORT`, `..._SKILLS_EXPORT`, `..._SKILLS_ALLOW_SHARING`, `..._SKILLS_ALLOW_PUBLIC_SHARING` | `False` | Seed `user.permissions` at first boot only; after that the stored value wins | `backend/open_webui/config.py:1741-1824` |
| `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS`, `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_GROUPS` | `True` | Seed the two sharing-target permissions | `backend/open_webui/config.py:1841-1846` |
| `ENABLE_COMMUNITY_SHARING` | `True` | Seeds `ui.enable_community_sharing` | `backend/open_webui/config.py:2096` |
| `DEFAULT_PROMPT_SUGGESTIONS` | unset | Seeds `ui.prompt_suggestions`; text that is not valid JSON is logged and treated as unset | `backend/open_webui/config.py:1678-1683` |
| `ENABLE_PLUGINS` | `True` | When off, event functions do not receive prompt and skill events (section 9) | `backend/open_webui/env.py:1186`; `backend/open_webui/events.py:1103-1107` |
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA`, `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` | `10` seconds; certificate checks on | Time limit and certificate checking when the server lists or loads a terminal's skills | `backend/open_webui/env.py:665-669`, `:684`; `backend/open_webui/utils/middleware.py:2863-2871`; `backend/open_webui/utils/terminals.py:247-268` |

### 7.3 Personal Settings

| Setting | Where | Effect | Source |
|---|---|---|---|
| **Insert Prompt as Rich Text** (`Paste inserted prompts as rich text when possible.`) | Settings › Interface, shown only when **Rich Text Input for Chat** is on; off by default | A prompt chosen from the `/` list is inserted as formatted Markdown (headings, lists, bold) instead of plain lines | `src/lib/components/common/InterfaceSettings.svelte:1661-1707`; `src/lib/i18n/locales/en-US/translation.json:2939-2940`, `:2963-2964`; `src/lib/components/chat/MessageInput.svelte:631-664` |
| **Hide Processing Details** (fork addition) | Settings › Interface | Hides tool calls, so a `view_skill` call is not visible in replies (section 12) | `src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`, `:199`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Function Calling** (`Default`, `Native`, `Legacy`) | Settings › General › advanced parameters, or the chat's controls | `Legacy` switches skills to the built-in-tools-off mode of section 5.26 | `builtin-native-tools.md`, section 7.4 |
| Workspace view filter | The `All` / `Created by you` / `Shared with you` selector | Remembered in the browser for all workspace lists | `src/lib/components/workspace/Prompts.svelte:309`, `:491-499`; `src/lib/components/workspace/Skills.svelte:222`, `:376-384` |

### 7.4 Per-Model Controls

| Control | Where | Effect | Source |
|---|---|---|---|
| **Skills** (default skills) | Model editor | Pre-selected in new chats and always added by the server (section 5.24) | `src/lib/components/workspace/Models/ModelEditor.svelte:353-358`, `:1203`; `backend/open_webui/utils/middleware.py:2772-2776` |
| **Builtin Tools** capability | Model editor › Capabilities; admin model defaults | Off means skills are sent in full instead of as a list (section 5.26) | `backend/open_webui/utils/middleware.py:2809-2813`; `builtin-native-tools.md`, sections 5.2 and 7.4 |
| **Function Calling** model parameter | Model editor › advanced parameters | As in section 7.3, when the person and the chat do not override it | `builtin-native-tools.md`, section 7.4 |
| **Prompt Suggestions** for the model | Model editor | Per-model suggestion cards; not workspace prompts | `workspace-models-and-model-access.md` |

### 7.5 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Workspace list page size | 30 prompts or skills per page | `backend/open_webui/routers/prompts.py:44`; `backend/open_webui/routers/skills.py:29`; `src/lib/components/workspace/Prompts.svelte:742-746`; `src/lib/components/workspace/Skills.svelte:601-605` |
| Version history page size | 20 versions per request, loaded as the column is scrolled | `backend/open_webui/routers/prompts.py:607`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:158-164` |
| `$` and `/` skill lists | The first 30 matching skills | `src/lib/components/chat/MessageInput/Commands/Skills.svelte:41-47`; `backend/open_webui/routers/skills.py:63-115` |
| `/` prompt list | Every active prompt the person can read, filtered in the browser by command | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:77-79`, `:119-131` |
| Waits before searching | 0.3 s for workspace searches; 0.2 s for the `/` and `$` lists; 0.5 s before a prompt's name, command or tags are saved | `src/lib/components/workspace/Prompts.svelte:129-139`; `src/lib/components/workspace/Skills.svelte:136-146`; `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:93-98`; `src/lib/components/chat/MessageInput/Commands/Skills.svelte:30-35`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:224-261` |
| Command characters (browser only) | `^[a-zA-Z0-9-_]+$` | `src/lib/components/workspace/Prompts/PromptEditor.svelte:121-124` |
| Skill ID characters (server) | `[a-z0-9_-]+` after lower-casing and turning spaces into hyphens | `backend/open_webui/routers/skills.py:167-174` |
| Names of copies | Prompt `{name} (Clone)` with command `{command}-clone`; skill `{name} (Clone)` with ID `{id}_clone` | `src/lib/components/workspace/Prompts.svelte:263-273`; `src/lib/components/workspace/Skills.svelte:176-190` |
| Export file names | `prompts-export-{timestamp}.json`, `prompt-export-{timestamp}.json`, `skills-export-{timestamp}.json`, `skill-{id}-export-{timestamp}.json` (milliseconds since 1970) | `src/lib/components/workspace/Prompts.svelte:122`, `:279`; `src/lib/components/workspace/Skills.svelte:99`, `:202` |
| Saved draft of the message box | Kept only while shorter than 5,000 characters | `src/lib/components/chat/Chat.svelte:4032`, `:4060-4069` |
| Lengths | No limit was found on prompt text, commands, names or skill instructions | `backend/open_webui/models/prompts.py:28-39`; `backend/open_webui/models/skills.py:20-32` |

## 8. Cron Jobs and Background Processes

**None found in code for prompts or skills themselves.** There is no crontab in this application, and
none of the seven startup loops (`inventory.md`, Background loops) touches the `prompt`,
`prompt_history` or `skill` tables. A search of the six back-end files in scope found no
`asyncio.create_task`, background task, scheduler or periodic job; every change (creating, saving a
version, restoring, sharing, switching, deleting) is written at save time, inside the request
(`backend/open_webui/routers/prompts.py`; `backend/open_webui/routers/skills.py`;
`backend/open_webui/models/prompts.py`; `backend/open_webui/models/prompt_history.py`;
`backend/open_webui/models/skills.py`; `backend/open_webui/utils/skills.py`). There is no clean-up of old
versions, no retention job and no indexing of skills into the vector store.

Three things happen after the request, and all belong to other areas:

| What | When | Effect here | Source |
|---|---|---|---|
| Event delivery | Each save publishes an event; event functions and webhooks are handed it as separate tasks, so a slow or failing receiver does not delay or fail the save | Section 9 | `backend/open_webui/events.py:1062-1066`, `:1159-1171`, `:1174-1202` |
| Timers, sub-agents and tool-approval resumes | A reply that sets a timer, delegates to a sub-agent or waits for tool approval keeps the request's skill ids and runs again later | The skills are looked up again when the follow-up runs, so a skill switched off or unshared in the meantime is skipped then | `backend/open_webui/utils/timers.py:106-117`; `backend/open_webui/utils/subagents.py:317-326`; `backend/open_webui/utils/tool_approval.py:165-180`; `backend/open_webui/main.py:1786-1795`; `builtin-native-tools.md`, sections 5.4, 5.7 and 5.8 |
| Automations | Run on the scheduler loop with their own prompt text | Automations do not use workspace prompts or skills | `backend/open_webui/utils/automations.py:382-395`; `automations-calendar-and-timers.md` (when written) |

In the browser, the only timed actions are the short waits of section 7.5 (search, the `/` and `$` lists,
and the prompt name autosave); nothing polls in the background.

## 9. Notifications and Emails

**No email** is sent by this area or anywhere in the application (`knowledgebase/tools/ground-truth.md`,
Contacts That Exist in the Repository). Prompts and skills create **no in-app or browser notification**:
none of their events is in the list that produces notifications
(`backend/open_webui/events.py:669-675`, `:1083-1086`). What people see are the pop-up messages of
section 10.

### 9.1 Application Events

Each successful change in the table below publishes an event, which is passed to every installed and
active **event function** (unless plugins are switched off) and to every admin **webhook** whose event filter matches
(`*`, a pattern such as `prompt.*` or `skill.*`, or an exact name; a webhook without a filter receives
everything) (`backend/open_webui/events.py:766-777`, `:1034-1060`, `:1103-1171`).

| Event | Message | Sent when | Extra data | Source |
|---|---|---|---|---|
| `prompt.created` | `Prompt created` | A prompt is created (also by import and clone) | name, command | `backend/open_webui/events.py:534-536`; `backend/open_webui/routers/prompts.py:182-188` |
| `prompt.updated` | `Prompt updated` | Content saved, or name, command or tags saved | name, command | `backend/open_webui/events.py:537-539`; `backend/open_webui/routers/prompts.py:303-309`, `:369-375` |
| `prompt.version_updated` | `Prompt version updated` | A version is made live | version id | `backend/open_webui/events.py:549-551`; `backend/open_webui/routers/prompts.py:417-423` |
| `prompt.access_updated` | `Prompt access updated` | Sharing changed in the Access dialog | name | `backend/open_webui/events.py:552-554`; `backend/open_webui/routers/prompts.py:483-489` |
| `prompt.enabled`, `prompt.disabled` | `Prompt enabled`, `Prompt disabled` | The switch is flipped | name, command | `backend/open_webui/events.py:543-548`; `backend/open_webui/routers/prompts.py:531-538` |
| `prompt.deleted` | `Prompt deleted` | A prompt is deleted | name, command | `backend/open_webui/events.py:540-542`; `backend/open_webui/routers/prompts.py:584-590` |
| `skill.created` | `Skill created` | A skill is created (also by import and clone) | name | `backend/open_webui/events.py:519-521`; `backend/open_webui/routers/skills.py:199-205` |
| `skill.updated` | `Skill updated` | A skill is saved, **or its sharing changes** (then with `access_updated: true`) | name | `backend/open_webui/events.py:522-524`; `backend/open_webui/routers/skills.py:326-332`, `:399-405` |
| `skill.enabled`, `skill.disabled` | `Skill enabled`, `Skill disabled` | The switch is flipped | name | `backend/open_webui/events.py:528-533`; `backend/open_webui/routers/skills.py:437-443` |
| `skill.deleted` | `Skill deleted` | A skill is deleted | name | `backend/open_webui/events.py:525-527`; `backend/open_webui/routers/skills.py:499-505` |
| `config.suggestions.updated` | `Config Suggestions updated` | An admin saves the default prompt suggestions | count | `backend/open_webui/events.py:94-98`; `backend/open_webui/routers/configs.py:831-838` |

Each event names the item by its id and carries the **actor's id, name, email address and role**
(`backend/open_webui/events.py:704`, `:974-985`, `:995-1031`), so webhook receivers hold personal data.
Webhook messages read, for example, `Prompt created ({id})` (`backend/open_webui/events.py:1041-1044`).
Deleting a single version publishes no event, and an import publishes one `prompt.created` or
`skill.created` per entry that succeeds (`backend/open_webui/routers/prompts.py:681-728`). Which webhooks and event functions
exist in production is data and **TO BE CONFIRMED**.

### 9.2 Live Updates

The server pushes nothing to other people's screens when a prompt or skill changes; there is no socket
event in this area. Others see a change when their screen next asks the server:

- the `/` list and the `$` list ask again 0.2 seconds after each keystroke, so a newly shared or renamed
  prompt or skill appears at once (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:93-131`;
  `src/lib/components/chat/MessageInput/Commands/Skills.svelte:30-47`);
- the Integrations menu keeps the list it read when the page loaded (section 5.25);
- workspace lists, the counts on the workspace tabs and an open prompt or skill page refresh only when
  reloaded or reopened (`src/routes/(app)/workspace/+layout.svelte:48-78`).

## 10. Error, Warning and Notice Messages (Verbatim)

Interpolated values are written as `{name}` using the source's variable name. Plain-key English text is
the key itself; dotted keys are quoted from `src/lib/i18n/locales/en-US/translation.json`. Back-end texts
reach people as red pop-ups on the screen that made the request, printed as the server sent them
(for example `src/lib/components/workspace/Prompts.svelte:250-253`;
`src/routes/(app)/workspace/skills/create/+page.svelte:24-27`). Two lists print a whole error object
instead, so a failure while loading the prompt or skill list shows `[object Object]` (read from code,
`src/lib/apis/prompts/index.ts:185-188`; `src/lib/apis/skills/index.ts:131-134`). Rows marked "Log" are
server log lines, not user messages.

### 10.1 Backend: Prompts Router (`backend/open_webui/routers/prompts.py`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `:150-167`; text `backend/open_webui/constants.py:69` | Creating, importing or cloning a prompt without **Prompts Access** or **Import Prompts** | Ask an admin for the permission | The person's groups and the default permissions (section 3.1) |
| `Uh-oh! This command is already registered. Please choose another command string.` | Error (HTTP 400) | `:194-197`, `:284-290`, `:357-363`; text `backend/open_webui/constants.py:51` | Another prompt anywhere on the site, visible or not, active or not, already uses that command (exact match); also a second clone or a repeated import | Choose another command | Section 11.2: an admin with admin bypass can search for the command |
| `Something went wrong :/` | Error (HTTP 400) | `:190-193`, `:312-315`, `:378-381`, `:426-429`, `:540-543`; text `backend/open_webui/constants.py:16-18` | The database refused the save (create, content save, name/command save, making a version live, switch) or the version does not belong to the prompt | Reload and try again | Server log at that time (section 10.8) |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `:238-241`, `:260-264`, `:334-338`, `:393-397`, `:450-454`, `:507-511`, `:560-564`, `:611-615`, `:648-652`, `:672-676`, `:691-695`, `:722-726`, `:742-746`, `:766-770`; text `backend/open_webui/constants.py:78` | The prompt or version no longer exists, or (when opening a prompt) the person cannot read it | Return to Workspace › Prompts and reload | Whether it was deleted or unshared; the prompt id from the address |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `:278-281`, `:351-354`, `:410-413`, `:467-470`, `:524-527`, `:577-580`, `:629-632`, `:666-669`, `:709-712`, `:760-763`; text `backend/open_webui/constants.py:70-72` | Saving, renaming, restoring a version, changing sharing, switching or deleting without write access; reading history without read access | Ask the owner for write access, or clone the prompt | The prompt's sharing (Access dialog) |
| `Cannot delete the active production version` | Error (HTTP 400) | `:714-719` | Deleting the live version (the menu normally blocks this) | Make another version live first | None |

Validation errors (for example an imported entry without `name`) come from the framework rather than this
file; the import shows them as raw JSON text (`src/lib/components/workspace/Prompts.svelte:430-432`).

### 10.2 Backend: Skills Router (`backend/open_webui/routers/skills.py`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `:129-138`, `:158-165`, `:300-303`, `:383-386`, `:450-454`, `:492-495`; text `backend/open_webui/constants.py:69` | **Export JSON** without **Export Skills**; creating, importing or cloning without **Skills Access** or **Import Skills**; saving, sharing, switching or deleting without write access | Ask an admin for the permission, or the owner for write access | Permissions (section 3.1) and the skill's sharing |
| `[ERROR: Invalid skill ID]` | Error (HTTP 400) | `:167-174`; format `backend/open_webui/constants.py:16-24` | The ID still contains characters other than `a-z`, `0-9`, `-` and `_` after lower-casing (usually from a JSON import) | Use letters, digits, hyphens and underscores | The ID in the file |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `:176-181`; text `backend/open_webui/constants.py:54` | Any skill already has that ID, including one the person cannot see; a second clone; a repeated import | Choose another ID | An admin can search Workspace › Skills for the ID |
| `[ERROR: Error creating skill]` | Error (HTTP 400) | `:207-219` | The database refused the new skill; the usual cause is a **name** another skill already has | Choose another name | Search Workspace › Skills for the name; server log (section 10.8) |
| `[ERROR: Error updating skill]` | Error (HTTP 400) | `:334-345` | The save was refused; the usual cause is renaming to a name another skill already has | Choose another name | As above |
| `[ERROR: Error toggling skill]` | Error (HTTP 400) | `:445-449` | The switch could not be saved; the list does not display it | Reload the page | Server log |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `:262-266`, `:283-287`, `:366-370`, `:455-459`, `:475-479`; text `backend/open_webui/constants.py:78` | The skill no longer exists | Return to Workspace › Skills and reload | Whether it was deleted |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `:257-261`; text `backend/open_webui/constants.py:70-72` | Opening a skill the person cannot read | Ask the owner to share it | The skill's sharing |

### 10.3 Workspace › Prompts (List, Editor and History)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Prompt created successfully` | Success | `src/lib/components/workspace/Prompts.svelte:256` | **Save & Create** (also after clone or a community import) succeeded | None | None |
| `Prompt updated successfully` | Success | `src/routes/(app)/workspace/prompts/[id]/+page.svelte:27` | **Save** in **Edit Prompt** succeeded | None | Whether **Set as Production** was ticked (section 5.5) |
| `Saved` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:252`, `:307` | The name, command or tags were saved automatically, or a sharing change was saved | None | None |
| `Production version updated` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:193` | **Set as Production** on a version | None | Command and sharing are not restored (section 5.6) |
| `Version deleted` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:204` | A version was deleted | None | None |
| `ID copied to clipboard` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:469` | The prompt id was clicked | None | None |
| `Deleted {name}` | Success | `src/lib/components/workspace/Prompts.svelte:301` | A prompt was deleted; `{name}` is its command | None | Deletion is permanent (section 5.13) |
| `Redirecting you to Open WebUI Community` | Notice | `src/lib/components/workspace/Prompts.svelte:210` | Row menu › **Share** (community sharing on) | Decide whether to publish outside MedIT GPT | Section 5.12 |
| `Only alphanumeric characters and hyphens are allowed in the command string.` | Error | `src/lib/components/workspace/Prompts/PromptEditor.svelte:113-115`, `:233-235` | The command contains a character other than letters, digits, `-` or `_`; on the prompt page the last saved command is put back | Remove spaces and other characters | None |
| `You do not have permission to edit this prompt.` | Error | `src/lib/components/workspace/Prompts/PromptEditor.svelte:84`, `:179` | A save or version change on a read-only prompt (the buttons are normally hidden) | Ask for write access | Sharing |
| `Delete prompt?` / `This will delete {command}.` | Confirmation | `src/lib/components/workspace/Prompts.svelte:378-388` | Row menu › **Delete** | Confirm or cancel | None |
| `Delete Version` / `Are you sure you want to delete this version? Child versions will be relinked to this version's parent.` | Confirmation | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:21-31` | Version menu › **Delete** | Confirm or cancel | None |
| `Cannot delete the production version` | Notice (tooltip) | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:54-62` | The version menu of the live version | Make another version live first | None |
| `No prompts found` / `Try adjusting your search or filter to find what you are looking for.` | Notice | `src/lib/components/workspace/Prompts.svelte:747-756` | Nothing matches the search, view and tag filters, or the person has no prompts | Clear the filters | Sharing; the view filter |
| `No history available` | Notice | `src/lib/components/workspace/Prompts/PromptEditor.svelte:735-738` | The prompt has no versions, or they failed to load | Reload | Server log |
| `Read Only` | Badge | `src/lib/components/workspace/Prompts.svelte:606-608`; `src/lib/components/workspace/Prompts/PromptEditor.svelte:439-443` | The person cannot change the prompt | Clone it to change a copy | Sharing |
| `Deleted User` | Label | `src/lib/components/workspace/Prompts.svelte:627-637` | The owner's account no longer exists | None | Section 6.7 |
| `Live` / `Update` | Label | `src/lib/components/workspace/Prompts/PromptEditor.svelte:501-504`, `:700-710` | The live version; a version saved without a commit message | None | None |
| `Only alphanumeric characters and hyphens are allowed - Activate this command by typing "/{COMMAND}" to chat input.` | Tooltip | `src/lib/components/workspace/Prompts/PromptEditor.svelte:573-575` | Hovering the name or command in **Create Prompt** | None | None |
| `Write a summary in 50 words that summarizes {{topic}}.` | Placeholder | `src/lib/components/workspace/Prompts/PromptEditor.svelte:338`, `:622`, `:629` | Empty **Prompt Content** box | None | None |
| `Describe what changed...` | Placeholder | `src/lib/components/workspace/Prompts/PromptEditor.svelte:352` | Empty **Commit Message** | None | None |
| `Discover a prompt` / `Discover, download, and explore custom prompts` | Link | `src/lib/components/workspace/Prompts.svelte:759-765` | Community sharing on | Section 5.12 | Section 14 |
| `Enabled` / `Disabled` | Tooltip | `src/lib/components/workspace/Prompts.svelte:721-725` | The row's switch | None | None |

### 10.4 Workspace › Skills (List, Editor, Import and Menus)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Skill created successfully` | Success | `src/routes/(app)/workspace/skills/create/+page.svelte:30` | **Save & Create** succeeded (also after a clone or Markdown import) | None | None |
| `Skill updated successfully` | Success | `src/routes/(app)/workspace/skills/edit/+page.svelte:28` | **Save** succeeded | None | None |
| `Saved` | Success | `src/lib/components/workspace/Skills/SkillEditor.svelte:105` | A sharing change was saved | None | None |
| `Skill deleted successfully` | Success | `src/lib/components/workspace/Skills.svelte:213` | A skill was deleted | None | Permanent (section 5.23) |
| `Skill imported successfully` | Success | `src/lib/components/workspace/Skills.svelte:296` | A JSON import finished, **including when every entry failed** | Check the list and any red messages shown before it | Section 11.16 |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Skills.svelte:300-302` | The `.json` file could not be read as JSON | Check the file | None |
| `[object Object]` | Error | `src/lib/components/workspace/Skills.svelte:291-293`; `src/lib/apis/skills/index.ts:21-29` | An imported entry lacks `id`, `name` or `content` (read from code) | Fix the file | The file's fields |
| `You do not have permission to edit this skill.` | Error | `src/lib/components/workspace/Skills/SkillEditor.svelte:52-56` | A save on a read-only skill (the button is normally hidden) | Ask for write access | Sharing |
| `Delete skill?` / `This will delete {name}.` | Confirmation | `src/lib/components/workspace/Skills.svelte:618-629` | Row menu › **Delete** | Confirm or cancel | None |
| `No skills found` / `Try adjusting your search or filter to find what you are looking for.` | Notice | `src/lib/components/workspace/Skills.svelte:606-615` | Nothing matches the search and view filter | Clear the filters | Sharing |
| `Inactive` | Badge | `src/lib/components/workspace/Skills.svelte:479-481` | The skill is switched off | Ask the owner to switch it on | None |
| `Read Only` | Badge | `src/lib/components/workspace/Skills.svelte:483-485`; `src/lib/components/workspace/Skills/SkillEditor.svelte:185-189` | The person cannot change the skill | None | Sharing |
| `Deleted User` | Label | `src/lib/components/workspace/Skills.svelte:508-518` | The owner's account no longer exists | None | Section 6.7 |
| `e.g. Code Review Guidelines` / `e.g. code-review-guidelines` / `e.g. Step-by-step instructions for code reviews` | Tooltip | `src/lib/components/workspace/Skills/SkillEditor.svelte:128`, `:148`, `:165` | Hovering the name, ID and description | None | None |
| `Enter skill instructions in markdown...` | Placeholder | `src/lib/components/workspace/Skills/SkillEditor.svelte:204` | Empty instructions box | None | None |
| `Editing language` | Tooltip | `src/lib/components/common/LanguageModeSelect.svelte:21-23` | The translation selector | None | None |

### 10.5 Chat Composer: Lists, Placeholders, Input Variables and the Skills Chip

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Commands` / `Prompts` / `Skills` | Headings | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:174-177`, `:442-445`, `:477-480`; `src/lib/components/chat/MessageInput/Commands/Skills.svelte:103-105` | The `/` and `$` pop-ups | None | None |
| `Create skill` / `Create a reusable terminal skill from this chat.` | Menu item and tooltip | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:383-411` | `/` with a terminal selected and chat content | Section 5.27 | Section 11.18 |
| `Terminal` | Label | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:512`; `src/lib/components/chat/MessageInput/Commands/Skills.svelte:136-138`; `src/lib/components/chat/SkillsModal.svelte:56-58` | A skill that lives on the selected terminal | None | None |
| `Failed to read clipboard contents` | Error | `src/lib/components/chat/MessageInput.svelte:284-288` | A prompt with `{{CLIPBOARD}}` and the browser refused clipboard access | Allow clipboard access for the site, or type the value | Browser permissions |
| `Location access not allowed` | Error | `src/lib/components/chat/MessageInput.svelte:311-318` | A prompt with `{{USER_LOCATION}}` and the browser refused location; `LOCATION_UNKNOWN` is inserted | Allow location for the site, or edit the text | Browser permissions |
| `Input Variables` | Dialog title | `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:17` | An inserted prompt still has `{{...}}` placeholders | Fill in the fields, then **Save** | Section 5.15 |
| `* required` | Label | `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:115-117` | A variable marked `required` | Fill it in | None |
| `Select an option` | Placeholder | `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:130-132` | A `select` variable without its own placeholder | Choose a value | None |
| `Enter value (true/false)` / `Enter hex color (e.g. #FF0000)` / `Enter value` | Placeholder | `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:160`, `:185`, `:261` | `checkbox`, `color` and `range` variables | Type or pick a value | None |
| `Enter coordinates (e.g. 51.505, -0.09)` | Placeholder | `src/lib/components/chat/MessageInput/InputVariablesModal.svelte:321-341` | A `map` variable (marked experimental in the code) | Type coordinates | None |
| `{COUNT} Available Skills` | Tooltip | `src/lib/components/chat/MessageInput.svelte:2390-2394` | The skills chip under the message box | Click to see the list | None |
| `Available Skills` | Dialog title | `src/lib/components/chat/SkillsModal.svelte:25` | The skills chip was clicked | None | None |
| `Search skills` / `No skills found` | Placeholder / notice | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:674-678` | The Integrations menu's skill list; nothing matches | Clear the search, or reload the page (section 5.25) | Sharing; whether the skill is active |

### 10.6 What the Model Receives: `view_skill` Results and Skill Instructions

These texts go to the model, not to a pop-up; people see them only inside the tool call's **Output** in
the reply (`src/lib/components/common/ToolCallDisplay.svelte:243-253`, `:330-336`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Skill '{id}' not found` | Tool error | `backend/open_webui/tools/builtin.py:3507-3509`, `:3518-3521` | The model asked for an id that does not exist, is inactive, or is a terminal skill the terminal did not return | Check the skill is active | Whether the skill was switched off or deleted |
| `Access denied` | Tool error | `backend/open_webui/tools/builtin.py:3523-3534` | The person can no longer read the skill (for example it was unshared after the chat started) | Ask the owner to share it | The skill's sharing |
| `Request context not available` / `User context not available` | Tool error | `backend/open_webui/tools/builtin.py:3495-3499` | Internal: the tool was called without the request or user (not expected in chats) | Escalate | Server log |
| `View Result from {NAME}` | Label | `src/lib/components/common/ToolCallDisplay.svelte:243-245` | A finished `view_skill` call (`{NAME}` is `view_skill`); hidden when **Hide Processing Details** is on | None | Section 12 |
| `[/skills:create] Skill creation requires a selected Open Terminal. Explain this briefly and do not try to create or update a skill.` | Instruction to the model | `backend/open_webui/utils/skills.py:133-138` | `/skills:create` sent without a selected terminal | Select a terminal | Terminal availability |
| `[/skills:create] The user tried to create a skill before this chat had any prior real content. Explain briefly that skill creation needs an existing chat with the workflow or source material already in it, then ask them to continue in a chat with content first.` | Instruction to the model | `backend/open_webui/utils/skills.py:139-144` | `/skills:create` as the first message of a chat | Use it in a chat that already shows the workflow | None |

The model replies in its own words to the two `/skills:create` instructions, so people do not see the
text above verbatim.

### 10.7 Admin Labels, Settings and Model Editor Text

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Warning: Enabling this will allow users to upload arbitrary code on the server.` | Warning (tooltip) | `src/lib/components/admin/Users/Groups/Permissions.svelte:183-197` | Hovering **Skills Access** in the permissions editor | Admin decision | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `This is a default user permission and will remain enabled.` | Notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:414-420` | A group editor where the default permissions already grant the key (shown for each key, for example **Skills Public Sharing**) | None: defaults cannot be removed by a group | `users-groups-roles-and-permissions.md`, section 3 |
| `Community Sharing` / `Allow users to share chats with the Open WebUI community.` | Setting label and description | `src/lib/components/admin/Settings/General.svelte:276-277`; `src/lib/i18n/locales/en-US/translation.json:2378-2379` | Admin Settings › General | Admin decision; it also controls prompt sharing (section 7.1) | Section 14 |
| `Insert Prompt as Rich Text` / `Paste inserted prompts as rich text when possible.` | Setting label and description | `src/lib/components/common/InterfaceSettings.svelte:1688`, `:1704`; `src/lib/i18n/locales/en-US/translation.json:2939-2940` | Settings › Interface, with **Rich Text Input for Chat** on | Personal choice | None |
| `To select skills here, add them to the "Skills" workspace first.` | Notice | `src/lib/components/workspace/Models/SkillsSelector.svelte:97-99` | The model editor's **Skills** section | Create or share a skill first | None |
| `Select Skill` / `Disable all` | Button labels | `src/lib/components/workspace/Models/SkillsSelector.svelte:40`, `:83-91` | The model editor's **Skills** section | None | None |

### 10.8 Server Log Lines

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error creating prompt: %s` | Log (exception) | `backend/open_webui/models/prompts.py:173-175` | Creating a prompt failed in the database; the person sees `Something went wrong :/` | None | Database health; the details after the colon |
| `Failed to restore prompt version: {e}` | Log (error) | `backend/open_webui/models/prompts.py:622-624` | Making a version live failed | None | As above |
| `Failed to delete prompt: {err}` | Log (error) | `backend/open_webui/models/prompts.py:678-680` | Deleting failed; the list reloads without a message | None | As above |
| `Error creating a new skill: {e}` | Log (exception) | `backend/open_webui/models/skills.py:146-148` | Creating a skill failed (for example a duplicate name); the person sees `[ERROR: Error creating skill]` | None | The details name the constraint |
| `Failed to create skill: {e}` | Log (exception) | `backend/open_webui/routers/skills.py:214-219` | An unexpected error while creating a skill | None | As above |
| `Error searching skills: {e}` | Log (exception) | `backend/open_webui/models/skills.py:313-315` | The skill list query failed; the list, `$` list and `/` list show no skills | None | Database health |
| `view_skill error: {e}` | Log (exception) | `backend/open_webui/tools/builtin.py:3543-3545` | `view_skill` failed unexpectedly; the model receives the error text | None | As above |
| `Error loading DEFAULT_PROMPT_SUGGESTIONS: {e}` | Log (exception, at startup) | `backend/open_webui/config.py:1679-1683` | `DEFAULT_PROMPT_SUGGESTIONS` is not valid JSON | None | The environment variable |
| `Event webhook failed for %s` / `Event function failed for %s` / `Event sink failed for %s` | Log (exception) | `backend/open_webui/events.py:1058-1059`, `:1155-1156`, `:1199-1202` | A webhook or event function could not process a prompt or skill event; the change itself is saved | None | The webhook or function named |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it explains, gathers identifiers and escalates; it does not change prompts, skills,
sharing, permissions or settings. Identify a prompt by its command and its id (the last part of the
prompt page's address) and a skill by its ID (shown after the `/` in the skill list); do not ask people to
paste prompt or skill text that may hold confidential or health information. Sections 3 and 5 hold the
detail behind each cause.

### 11.1 "My slash command doesn't show up when I type /"

**Symptom.** Typing `/` and part of the command shows no matching entry under `Prompts`, or no pop-up at
all.

**Likely causes, in order.**
1. The person is typing the prompt's **name**; the `Prompts` group matches only the **command**
   (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:77-79`).
2. The prompt is switched off: disabled prompts are left out of every `/` list
   (`backend/open_webui/models/prompts.py:200-211`, `:247`).
3. The prompt is not, or no longer, shared with them: shared with a group they are not in, unshared, or a
   collaborator's save removed **Public** (sections 5.5 and 11.5).
4. The command was changed; the old command is not kept as an alias (section 5.4).
5. The `/` is not at the start of the message or after a space, or the person pressed Enter on a built-in
   command listed above the prompts (section 5.14).
6. They are in a **channel**, where choosing a prompt behaves differently (section 11.20).
7. The list could not be fetched; the pop-up silently keeps whatever it had before
   (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:119-131`).

**Diagnostic steps.** Ask for the exact command and name. If they have Workspace › Prompts, ask them to
search for the command there (view filter `All`) and say whether the row's switch is on and whether it
shows `Read Only`. Ask them to type `/` at the very start of an empty message box followed by the first
letters of the command. Ask who shared it and whether it was shared with them or with a group. Ask them
to reload the page once.

**Resolution.** Explain that `/` matches commands, not names. If the prompt is switched off or not shared,
the owner (or someone with write access) can switch it on or share it again.

**Escalation.** The command and name, the person's email, the owner's name if known, and screenshots of
the `/` pop-up and of the prompt's row in Workspace › Prompts.

### 11.2 "It says the command is already taken"

**Symptom.** Saving a new prompt, a clone, an import, or a changed command shows
`Uh-oh! This command is already registered. Please choose another command string.`

**Likely causes, in order.**
1. Another person's prompt uses that command; commands are unique across the whole site, and the other
   prompt can be invisible to them (section 5.3).
2. Their own switched-off prompt still holds it (disabled prompts keep their command).
3. A prompt left by a deleted account holds it (section 6.7).
4. They cloned the same prompt twice (`{command}-clone`) or imported the same file twice.

**Diagnostic steps.** Ask for the exact command, including capitals (`Summarize` and `summarize` are
different commands). Ask them to search Workspace › Prompts for it with the view filter `All`; the search
matches commands, so their own prompt, enabled or not, will appear if it is theirs.

**Resolution.** Suggest a different command (for example with a department or course suffix). If the
holder is their own prompt, they can rename or delete it themselves. Tier 1 does not touch other people's
prompts.

**Escalation.** The command, the person's email and the time. Only an admin with admin bypass sees every
prompt (section 3.2) and can find the holder, which may show as `Deleted User`; whether to rename or
remove someone else's prompt is for the service owner (**TO BE CONFIRMED** who decides).

### 11.3 "It says only alphanumeric characters and hyphens are allowed"

**Symptom.** `Only alphanumeric characters and hyphens are allowed in the command string.` when saving; on
the prompt page the command jumps back to the last saved value.

**Likely causes, in order.**
1. The command contains a space, a full stop, an accented letter, a `/` in the middle or other punctuation.
   Underscores are allowed although the message does not say so (section 4.1).
2. The prompt was imported with a command the editor does not accept; every later save of its text then
   fails until the command is corrected (section 5.3).

**Diagnostic steps.** Ask for the command exactly as typed and look for spaces and punctuation.

**Resolution.** Use only letters, digits, hyphens and underscores. For an imported prompt, fix the command
on the prompt page first, then edit the text.

**Escalation.** Rarely needed: the prompt id and a screenshot.

### 11.4 "The variables box doesn't appear" or "A box asks me for values I didn't expect"

**Symptom.** A prompt's `{{...}}` placeholders stay in the message box without the **Input Variables**
form, or the form asks for something such as `USER_BIO`.

**Likely causes, in order.**
1. The placeholder text was typed or pasted by hand; the form opens only for text inserted from the `/`
   list, a suggestion card or a follow-up (section 5.15).
2. The placeholder's name contains a space, or a `|` or `}` in the wrong place (for example `{{my topic}}`),
   so it is not recognized (`src/lib/utils/index.ts:1731-1751`).
3. It is a built-in placeholder such as `{{CURRENT_DATE}}` or `{{USER_NAME}}`, which is filled in
   automatically with no form (section 4.2).
4. The form was closed with **Cancel** or the X; it does not reopen until the prompt is inserted again.
5. They are in a channel (section 11.20).
6. For an unexpected form: a built-in placeholder had no value (for example `{{USER_BIO}}` with an empty
   profile, or `{{CLIPBOARD}}` after the browser refused clipboard access), so it is asked for instead.
   A form titled **Chat Variables** is a different feature defined by the model
   (`chat-composer-and-message-display.md`, section 5.8).

**Diagnostic steps.** Ask for the prompt's command and how it was inserted (picked from `/`, or pasted). Ask
the owner, or the person if they can open the prompt, to read out the exact placeholder spelling. Note the
form's title.

**Resolution.** Pick the prompt from the `/` list. Placeholder spelling is the owner's to fix (for example
`{{topic}}` or `{{my_topic}}`). Profile values come from the person's own account settings; otherwise they
can type the value in the form.

**Escalation.** The prompt's id or command, the placeholder as written, and a screenshot of the message box
after inserting the prompt.

### 11.5 "I can't see a prompt someone shared" or "My colleague can't see the prompt I shared"

**Symptom.** A prompt the owner says is shared does not appear in the recipient's Workspace › Prompts or
`/` list.

**Likely causes, in order.**
1. The sharing entries never took effect: without **Prompts Sharing** the dialog has no access list, and
   the server silently drops **Public** without **Prompts Public Sharing** and people or groups without the
   two sharing-target permissions (section 3.1; `users-groups-roles-and-permissions.md`, section 5.17).
2. It was shared with a group the recipient is not in.
3. The prompt is switched off: it shows in the workspace list but not in `/`.
4. The recipient lacks **Prompts Access**, so the workspace section is hidden; shared prompts still work
   in `/` (section 3.1).
5. A collaborator's later text save re-applied the sharing with their own permissions and removed entries
   (section 5.5).
6. The list is narrowed by a remembered view filter (`Created by you`), a search, a tag or a later page.

**Diagnostic steps.** Ask the owner to open the prompt's **Access** dialog and read out, without changing
anything, who is listed and with what access. Ask the recipient to type `/` and the start of the command,
and to set the view filter to `All` and clear the search.

**Resolution.** The owner, or someone with write access, can share it again. If the owner lacks the sharing
permission, that is an admin decision.

**Escalation.** The command and id, the owner's and recipient's emails, the group name, and a screenshot of
the Access dialog.

### 11.6 "I don't see Prompts or Skills in the Workspace" or "Create says 401 Unauthorized"

**Symptom.** No **Prompts** or **Skills** tab; opening `/workspace/prompts` or `/workspace/skills` lands on
the home page; or saving a new item answers `401 Unauthorized`.

**Likely causes, in order.**
1. The person lacks **Prompts Access** or **Skills Access**, which are off in code (section 3.1;
   `src/routes/(app)/workspace/+layout.svelte:80-102`).
2. The permission was granted after their page loaded.
3. For imports: **Import Prompts** or **Import Skills** is missing; for **Export JSON** of skills,
   **Export Skills**.

**Diagnostic steps.** Ask which workspace tabs they see and whether reloading changes anything; ask which
group they expect to grant access.

**Resolution.** Explain that admins grant these permissions. Shared prompts and skills can be used in chat
meanwhile (`/`, `$` and the Integrations menu).

**Escalation.** Email, the expected group and a screenshot of the Workspace page.

### 11.7 "I saved my prompt but the old text is still used"

**Symptom.** After **Save** in **Edit Prompt**, the `/` list still inserts the previous text.

**Likely causes, in order.**
1. **Set as Production** was unticked, so the new text became a version that is not live (section 5.5).
2. Someone with write access made an older version live afterwards (section 5.6).
3. They changed only the name on the prompt page, which saves no version (section 5.4).
4. They expect text already sent in earlier chats to change; inserted text is copied into the message.

**Diagnostic steps.** Ask them to open the prompt page and say which History entry is marked `Live`, and
the first seven characters of the version shown.

**Resolution.** The owner or a writer can press **Set as Production** on the wanted version.

**Escalation.** The prompt id, the version ids and a screenshot of the History column.

### 11.8 "I restored an old version but the command or sharing didn't come back"

**Symptom.** After **Set as Production** on an older version the name and text changed back, but the
command and the sharing did not.

**Likely causes, in order.** By design: restoring brings back the name, text and tags only
(`backend/open_webui/models/prompts.py:607-615`).

**Diagnostic steps.** None needed beyond confirming which version was restored.

**Resolution.** Explain; the owner can change the command on the prompt page and the sharing in **Access**.

**Escalation.** Not needed unless the history itself looks wrong (prompt id, screenshot).

### 11.9 "Public sharing disappeared after a colleague edited it"

**Symptom.** A prompt or skill that was **Public**, or shared with certain people or groups, is no longer,
and nobody remembers changing the sharing.

**Likely causes, in order.**
1. A collaborator with write access saved the text; the save re-applied the sharing with the collaborator's
   permissions and dropped what they may not grant (sections 5.5 and 5.19).
2. Someone with write access changed the sharing in the Access dialog.

**Diagnostic steps.** For a prompt, ask the owner to look at the History column: the newest version shows
who saved it and when. Skills keep no history. Ask the owner to read out the current Access entries.

**Resolution.** The owner can share it again if they have the permission. Explain that collaborators who
lack **Prompts Public Sharing** or **Skills Public Sharing** remove Public by saving.

**Escalation.** The item's id, the time, the collaborators' names from History. Changing permissions is an
admin decision.

### 11.10 "I can't delete this version"

**Symptom.** In the version menu **Delete** is greyed out with `Cannot delete the production version`, or
the server answers `Cannot delete the active production version`.

**Likely causes, in order.** The version is the live one; or the person has read-only access (no version
menu at all).

**Diagnostic steps.** Ask whether the version shows `Live`.

**Resolution.** Make another version live first, then delete this one.

**Escalation.** Not needed.

### 11.11 "The on/off switch flips back" or "I switched it off but it's on again"

**Symptom.** A prompt's or skill's switch returns to its old position after a reload, or a skill someone
switched off is active again.

**Likely causes, in order.**
1. The person cannot change the item. Prompt rows show the switch even on `Read Only` rows; the server
   refuses and no message appears (section 5.8). Skill rows hide it from read-only viewers, but a refused
   change after access was removed is equally silent (section 5.21).
2. For a skill: someone saved the skill from an editor page opened before it was switched off, which writes
   the old state back (section 5.19).
3. Another person with write access switched it.

**Diagnostic steps.** Ask them to reload and check whether the row shows `Read Only`; ask who else can edit
it.

**Resolution.** Explain; only the owner, people with write access and admins can switch it.

**Escalation.** The item's id and command or ID, and the time.

### 11.12 "Importing prompts did nothing" or "It showed a block of text"

**Symptom.** **Import JSON** on Workspace › Prompts adds nothing, or shows a red message full of JSON text.

**Likely causes, in order.**
1. The file is not valid JSON, or is not a list; nothing visible happens (section 5.11).
2. The entries name their title `title` (older Open WebUI exports) rather than `name`; each entry then
   shows a validation error as raw JSON text.
3. The commands are already registered (the file was imported before).
4. The person lacks **Import Prompts** (`401 Unauthorized`).

**Diagnostic steps.** Ask where the file came from (which system and version) and for the red messages
shown; do not ask for the file's prompt text.

**Resolution.** Explain that the import takes only the command, name and text of each entry, and that tags,
sharing and history are not imported. A file exported from MedIT GPT's own **Export JSON** has the expected
shape.

**Escalation.** The file name and source, the messages shown and the time.

### 11.13 "The model ignores my skill"

**Symptom.** Replies do not follow a skill the person switched on, mentioned or expects from the model.

**Likely causes, in order.**
1. Native mode (the usual case): the model sees only the skill's name and description and chose not to
   load it with `view_skill`; there is no `view_skill` entry in the reply. A vague description makes this
   more likely (section 5.26).
2. The skill was picked from the `/` list; read from code, that pick is not treated as a skill mention
   (section 5.25).
3. The skill is switched off (`Inactive`), which removes it from every chat (section 5.21).
4. The person cannot read the skill: a model's default skill owned by someone else and not shared with
   them, or an admin relying on admin bypass, which does not apply in chats (sections 3.2 and 5.24).
5. **Hide Processing Details** is on, so the `view_skill` call is hidden and the skill may in fact have
   been used (section 12).
6. The instructions use placeholders such as `{{USER_NAME}}`, which are not filled in for skills, or they
   conflict with the model's system prompt or another skill (section 5.26).
7. It is a terminal skill and the terminal is not selected or not reachable (section 5.26).

**Diagnostic steps.** Ask for the skill's name and ID, how it was added (Integrations switch, `$` chip,
`/` list or the model's defaults) and which model was used. Ask whether the skill shows `Inactive` in
Workspace › Skills, and whether it appears in their Integrations menu. Ask them to look at the reply for a
tool entry reading `View Result from view_skill`, with **Hide Processing Details** off.

**Resolution.** Suggest typing `$` and choosing the skill in the message: a `$` mention gives the model the
full instructions for the rest of the chat. The owner can improve the description, switch the skill on or
share it.

**Escalation.** The skill ID, the model, the chat's id (from its address, not its content), the time, and
screenshots of the message box chips and of the reply's tool entries.

### 11.14 "I switched a skill off in the chat but the model still follows it"

**Symptom.** After switching a skill off in the Integrations menu, replies still follow it.

**Likely causes, in order.**
1. It is one of the model's default skills; the server adds those on every message whatever the switch
   shows (section 5.24).
2. Native mode lists every active skill the person can read, so the model may load it anyway (section
   5.26).
3. It was mentioned with `$` earlier in the same chat; earlier mentions keep loading it.
4. The skill's text from an earlier `view_skill` call is still part of the conversation.

**Diagnostic steps.** Ask which model is used and whether its editor lists the skill under **Skills** (if
they can open it); ask whether a `$` chip was used earlier in the chat.

**Resolution.** Start a new chat without mentioning the skill. Removing a model default is for the model's
owner; switching the skill off in the workspace affects everyone and is for the skill's owner.

**Escalation.** The model, the skill ID and the chat's id. Confirming behaviour 1 is listed in section 14.

### 11.15 "Creating a skill fails"

**Symptom.** **Save & Create** on a skill shows a red message, or seems to do nothing.

**Likely causes, in order.**
1. `Uh-oh! This id is already registered. Please choose another id string.`: the ID is taken, possibly by a
   skill the person cannot see, or by an earlier clone (`{id}_clone`).
2. `[ERROR: Error creating skill]`: the **name** is already used by another skill (section 5.17).
3. `[ERROR: Invalid skill ID]`: the ID has characters other than `a-z`, `0-9`, `-` and `_` (usually from an
   imported file).
4. `401 Unauthorized`: no **Skills Access** or **Import Skills**.
5. Nothing happens: a required field is empty, or the default-language name is blank while a translation
   was being edited, so the editor switched back to `Default` (section 5.17).

**Diagnostic steps.** Ask for the exact message, the name and the ID.

**Resolution.** Change the ID or the name. Explain that both are unique across the site.

**Escalation.** The name and ID, the message and the time; an admin can search Workspace › Skills for the
holder.

### 11.16 "The skill import said it worked, but nothing appeared"

**Symptom.** `Skill imported successfully` appears but the list has no new skill, or a Markdown import
opened an editor and nothing was saved.

**Likely causes, in order.**
1. Every entry failed; the success message appears regardless. The red messages shown before it give the
   reasons: `Uh-oh! This id is already registered. Please choose another id string.`,
   `[ERROR: Invalid skill ID]`, `[ERROR: Error creating skill]`, `401 Unauthorized`, or `[object Object]`
   for an entry missing `id`, `name` or `content` (section 5.18).
2. A `.md` file only opens the create page; nothing is saved until **Save & Create**.

**Diagnostic steps.** Ask which file type was used and for the red messages.

**Resolution.** Explain; fix the IDs or names, or press **Save & Create** after a Markdown import.

**Escalation.** The file name and source and the messages.

### 11.17 "My skill isn't in the $ list or the Integrations menu"

**Symptom.** A skill the person owns or was given does not appear when they type `$`, or under
Integrations › Skills.

**Likely causes, in order.**
1. The Integrations menu keeps the list it read when the page loaded; a skill created elsewhere or shared a
   moment ago appears after a reload (section 5.25).
2. The skill is switched off: the Integrations menu hides inactive skills (the `$` list still shows them).
3. The `$` and `/` lists show only the first 30 matching skills; typing more of the name narrows them.
4. The skill is not shared with the person, or is a terminal skill and that terminal is not selected.

**Diagnostic steps.** Ask them to reload the page, type `$` and several letters of the name, and check
Workspace › Skills (if they have access) for an `Inactive` badge.

**Resolution.** Reload; type more letters; ask the owner to share it or switch it on.

**Escalation.** The skill name and ID, the person's email and the owner if known.

### 11.18 "/skills:create says I need a terminal" or "Create skill isn't in the list"

**Symptom.** The model answers that skill creation needs a selected Open Terminal or an existing chat, or
the `/` list has no **Create skill** entry.

**Likely causes, in order.**
1. No terminal is selected in the chat (section 5.27).
2. The chat has no earlier content; sent as the first message, `/skills:create` only makes the model
   explain that it needs an existing chat.
3. Read from code, the browser decides whether the chat has content when the message box first appears, so
   the entry may be missing until the page is reloaded (section 14).

**Diagnostic steps.** Ask whether a terminal is selected under the message box and whether the chat already
shows the workflow.

**Resolution.** Select a terminal and use the command in a chat that already contains the work; typing
`/skills:create` followed by a short request also works. Explain that the result is a terminal skill, not
a Workspace skill.

**Escalation.** The terminal's name, the chat's id and the time.

### 11.19 "The prompt filled in my name, email or location"

**Symptom.** After choosing a prompt the message box contains the person's own name, email address,
location or other profile details, and they are worried about who can see them.

**Likely causes, in order.** The prompt contains `{{USER_NAME}}`, `{{USER_EMAIL}}`, `{{USER_LOCATION}}`,
`{{USER_BIO}}`, `{{USER_GENDER}}`, `{{USER_BIRTH_DATE}}` or `{{USER_AGE}}` (or `{{CLIPBOARD}}`), which the
browser fills from the person's own account, location and clipboard (sections 4.2 and 6.6).

**Diagnostic steps.** Ask which prompt (command) and which details appeared; do not ask them to send the
details themselves.

**Resolution.** Explain that the values are filled in their own browser, are visible before sending and can
be deleted from the message box; nothing is sent until they send it, and the prompt's author does not
receive them. Once sent, the text is part of their chat and goes to the model like any message. Location
needs the browser's permission, which they can refuse.

**Escalation.** If a prompt appears designed to collect personal details from many people, or details were
sent where they should not have been, treat it as a possible privacy incident and refer it (U of T Privacy
Office, privacy.utoronto.ca; the internal route is **TO BE CONFIRMED**) with the prompt's command and id
only.

### 11.20 "Choosing a prompt in a channel inserts a chip instead of the text"

**Symptom.** In a channel's message box, `/` lists prompts, but choosing one inserts a small chip such as
`$summarize-paper` instead of the prompt's text.

**Likely causes, in order.** Read from code: the channel message box uses the same `/` list but has no
handler for prompts, so the editor inserts a mention chip carrying the command
(`src/lib/components/channel/MessageInput.svelte:594-626`; `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:113-119`;
`src/lib/components/common/RichTextInput.svelte:117-127`, `:297-302`). Confirming this is listed in section
14.

**Diagnostic steps.** Ask whether it happens in a channel or in a chat, and for a screenshot.

**Resolution.** Suggest copying the text with **Copy Prompt** in Workspace › Prompts (if they have access)
and pasting it, or using the prompt in a chat.

**Escalation.** The channel's name, the prompt's command and the screenshot, as a product issue.

### 11.21 "I deleted a prompt or skill by mistake. Can it be restored?"

**Symptom.** A prompt or skill is gone after **Delete**, often after a **Shift**-click on the bin icon,
which deletes without asking.

**Likely causes, in order.** Deletion is permanent: the item, all prompt versions and all sharing are
removed, with no recycle bin (sections 5.13 and 5.23).

**Diagnostic steps.** Ask for the command or skill ID, the approximate time and whether anyone has an export
file.

**Resolution.** Explain that tier 1 cannot restore it. An earlier export can be imported again: for prompts
only the command, name and text come back; for skills the sharing comes back too. Chats that used the prompt
keep its text.

**Escalation.** The command or ID, the owner's email and the time of deletion; restoring from a database
backup (**TO BE CONFIRMED** whether backups exist) is for the platform maintainer.

## 12. Local Customisations

Checked with read-only `git diff main...uoft` (fork commits) and `git diff` (uncommitted working tree)
over every file in section 13.1, plus the consulted files `backend/open_webui/utils/middleware.py`,
`backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/tools.py`, `backend/open_webui/events.py`,
`src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte`,
`src/lib/components/chat/Chat.svelte`, `src/lib/components/channel/MessageInput.svelte`,
`src/lib/components/common/RichTextInput.svelte`, `src/lib/components/common/InterfaceSettings.svelte`,
`src/lib/components/common/ToolCallDisplay.svelte` and `src/lib/components/workspace/Models/`.

- **No file in this area's scope differs from upstream Open WebUI v0.11.4**, in the fork commits or in the
  uncommitted working tree. Prompts, versions, skills, sharing, import and export, the `/` and `$` lists,
  the Input Variables form, skill delivery and `view_skill` behave as upstream.
- **Hide Processing Details** (fork commit `aeed1832c`; `backend/open_webui/models/users.py:99-100`). With
  this Interface setting on (`Hide Processing Details`, described as `Show "Thinking..." instead of status
  updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden
  afterwards. Tool approval requests and images or embeds from tools still appear.`), a reply no longer
  shows the `view_skill` tool call or its `View Result from view_skill` entry
  (`src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`, `:199`;
  `src/lib/i18n/locales/en-US/translation.json:2923-2924`). When someone reports that the model "never
  reads" a skill, ask whether this setting is on before concluding the skill was ignored (section 11.13).
  In the working tree `ToolCallDisplay.svelte` reads the setting itself instead of receiving it from its
  parent; the effect is the same. The same fork commit also hides the running task list above the message
  box (`src/lib/components/chat/MessageInput.svelte:1791`), which does not concern prompts or skills.
- **Branding.** The browser tabs read `Prompts / MedIT GPT` and `Skills / MedIT GPT` with the fork's
  default name (`src/lib/components/workspace/Prompts.svelte:372-374`;
  `src/lib/components/workspace/Skills.svelte:262-264`; `backend/open_webui/env.py:951`), and event webhooks
  are sent under the app name (`backend/open_webui/events.py:1038`). The community features keep the
  upstream wording `Redirecting you to Open WebUI Community` and the community-sharing description, which
  sit next to licence comments that stay as they are (`src/lib/components/workspace/Prompts.svelte:206-210`;
  `CLAUDE.md`, Conventions). The `/skills:create` instructions sent to the model still speak of "Open WebUI"
  skills (`backend/open_webui/utils/skills.py:37-38`, `:88-90`); people see this only if the model repeats it.
- **Inline Citations** (same fork commit) has no effect on prompts or skills.
- The other uncommitted changes (chat message rendering, `structuredOutput.ts`, `src/lib/i18n/index.ts`, and
  the `Chat.svelte` change that keeps a reply open when it resumes after a tool approval) do not change
  anything described here (`src/lib/components/chat/Chat.svelte:2847-2850`).

## 13. Source File Index

### 13.1 Files in Scope

| File | What it does in this area |
|---|---|
| `backend/open_webui/routers/prompts.py` | Prompt API: list for `/` and export, tags, paged workspace list with `write_access`, create, read, content save (version), name/command/tag save, make a version live, sharing, switch, delete, history list, one version, delete a version, version comparison (not reachable, section 14) |
| `backend/open_webui/models/prompts.py` | `prompt` table; create with first version; lookups by id and command; active lists with owner and sharing; workspace search (name, command, text, owner) with view, tag and sort filters; content save with version; metadata save; restore; switch; delete with history and sharing; tag lists |
| `backend/open_webui/models/prompt_history.py` | `prompt_history` table; create, list (with authors), read, latest, count, line comparison, delete all, delete one with re-linking |
| `backend/open_webui/routers/skills.py` | Skill API: list for chats, paged workspace list, export, create (ID rules, uniqueness), read, save, sharing, switch, delete |
| `backend/open_webui/models/skills.py` | `skill` table and `meta` (translations, tags); create, read by id and name, lists filtered by access, workspace search (name, description, id, owner), save, switch, delete |
| `backend/open_webui/utils/skills.py` | `$` mention patterns, extracting and tidying mentions, `/skills:create` instructions, standards and gate texts |
| `src/lib/components/workspace/Prompts.svelte` | Workspace › Prompts list: actions (Create, Import JSON, Export JSON), search, view and tag filters, sorting, rows and badges, copy, Shift-delete, switch, clone, export, community share and discovery, import, create dialog |
| `src/lib/components/workspace/Prompts/PromptEditor.svelte` | Create Prompt form; prompt page with name/command/tag autosave, Access, Edit Prompt dialog (content, commit message, Set as Production), History column, version view, restore and delete |
| `src/lib/components/workspace/Prompts/PromptMenu.svelte` | Row menu: Edit, Share (community), Clone, Export, Delete |
| `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte` | Version menu and the Delete Version confirmation |
| `src/lib/components/workspace/Skills.svelte` | Workspace › Skills list: actions, search, view filter, sorting, rows and badges, Shift-delete, switch, clone, export, JSON and Markdown import, delete confirmation |
| `src/lib/components/workspace/Skills/SkillEditor.svelte` | Skill editor: name, ID, description, translations, front-matter copy, Access, instructions, read-only view, save |
| `src/lib/components/workspace/Skills/SkillMenu.svelte` | Row menu: Edit, Clone, Export, Delete |
| `src/routes/(app)/workspace/prompts/+page.svelte`, `create/+page.svelte`, `[id]/+page.svelte` | Prompt list, list with the create dialog open, and one prompt's page (load, save, read-only) |
| `src/routes/(app)/workspace/skills/+page.svelte`, `create/+page.svelte`, `edit/+page.svelte` | Skill list, create page (with clone and import pre-fill) and edit page (`?id=`) |
| `src/lib/components/chat/SkillsModal.svelte` | The **Available Skills** dialog behind the skills chip |
| `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte` | The `/` pop-up: built-in commands (including **Create skill**), prompts matched by command, skills |
| `src/lib/components/chat/MessageInput/Commands/Skills.svelte` | The `$` pop-up of skills, with terminal skills |
| `src/lib/components/chat/MessageInput/Commands/Prompts.svelte` | An older prompts-only pop-up; no component imports it in this release |
| `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte`, `Emojis.svelte`, `Knowledge.svelte`, `Models.svelte` | The `@`, `:` and `#` pop-ups in the same folder; checked here only for prompt and skill content (none); described in `chat-composer-and-message-display.md` |
| `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte` | Chooses the pop-up by trigger character and turns a choice into an inserted prompt, a command or a skill chip |
| `src/lib/components/chat/MessageInput/InputVariablesModal.svelte` | The **Input Variables** form and its field types (also reused for Chat Variables) |
| `src/lib/utils/index.ts` | `slugify`, `extractInputVariables`, `splitProperties`, `parseVariableDefinition`, `parseJsonValue`, `parseFrontmatter`, `formatSkillName`, `getUserPosition`, `getAge`, the date and time helpers, `extractCurlyBraceWords` |
| `src/lib/apis/prompts/index.ts` | Browser calls for every prompt endpoint (removes a leading `/` from new commands) |
| `src/lib/apis/skills/index.ts` | Browser calls for every skill endpoint |
| `backend/open_webui/config.py` (settings for this area) | Prompt and skill permission defaults, prompt suggestions, community sharing, admin bypass |

### 13.2 Files Consulted Outside Scope

| File | Why |
|---|---|
| `backend/open_webui/utils/middleware.py` | How skills are gathered and delivered; mention tidying; empty-message fallback; `/skills:create`; skill ids kept for tool approval |
| `backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/tools.py` | `view_skill` and when it is offered |
| `backend/open_webui/utils/terminals.py`, `src/lib/apis/terminal/index.ts` | Terminal skills |
| `backend/open_webui/utils/misc.py` | How skill text is appended to the system message |
| `backend/open_webui/utils/timers.py`, `backend/open_webui/utils/subagents.py`, `backend/open_webui/utils/tool_approval.py`, `backend/open_webui/utils/automations.py` | Follow-up runs that carry skill ids; automations' own prompt text |
| `backend/open_webui/events.py` | Prompt and skill events, sinks, webhook matching, actor fields |
| `backend/open_webui/models/access_grants.py`, `backend/open_webui/utils/access_control/__init__.py` | Sharing rows, list filters and the share filter |
| `backend/open_webui/constants.py` | Message texts |
| `backend/open_webui/main.py`, `backend/open_webui/routers/configs.py`, `backend/open_webui/env.py`, `backend/open_webui/models/users.py` | Router mounting and features sent to the browser; prompt suggestions; environment settings; the user record in lists and history |
| `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py`, `922e7a387820_add_group_table.py`, `374d2f66af06_add_prompt_history_table.py`, `f1e2d3c4b5a6_add_access_grant_table.py`, `a1b2c3d4e5f6_add_skill_table.py`, `461111b60977_add_missing_primary_keys_to_legacy_.py` | Schema history |
| `src/lib/components/chat/MessageInput.svelte` | Placeholder filling, the `/` and `$` handlers, prompt insertion, the skills chip, **Create skill** |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Skill switches in a chat |
| `src/lib/components/chat/Chat.svelte` | Model default skills, skill ids sent with each message, the saved draft, terminal changes, Chat Variables |
| `src/lib/components/channel/MessageInput.svelte` | The `/` list in channels |
| `src/lib/components/common/RichTextInput.svelte`, `src/lib/components/common/RichTextInput/suggestions.ts` | How chips are drawn and turned into message text; how a choice reaches the editor |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte` | How mentions look in sent messages |
| `src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/components/common/InterfaceSettings.svelte` | Tool call labels; Insert Prompt as Rich Text and Hide Processing Details |
| `src/lib/components/common/LanguageModeSelect.svelte`, `src/lib/components/common/LocalizedField.svelte`, `src/lib/utils/localizedContent.ts` | Skill translations |
| `src/lib/components/workspace/Models/SkillsSelector.svelte`, `src/lib/components/workspace/Models/ModelEditor.svelte` | Model default skills |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | Permission labels and the Skills Access warning |
| `src/lib/components/admin/Settings/General.svelte`, `src/lib/components/admin/Settings/Events.svelte`, `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | Community Sharing, Webhooks, Prompt Suggestions |
| `src/routes/(app)/workspace/+layout.svelte` | Workspace tabs, counts and redirects |
| `src/lib/constants.ts` | Community site origins |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys (every plain key in scope is empty there, so the key itself is shown) |
| `node_modules/@tiptap/extension-mention/src/mention.ts`, `node_modules/@tiptap/extension-mention/src/utils/get-default-suggestion-attributes.ts`, `node_modules/@tiptap/suggestion/src/suggestion.ts` | Third-party editor code: the default `@` chip marker and how a choice is passed on (section 5.25) |

## 14. Open Questions

The code cannot settle the items below. Each heading says who can answer. Every item marked
**TO BE CONFIRMED**, "read from code" or "listed in section 14" earlier in this document is repeated here.

### 14.1 Live Data (Answered by an Admin or a Read-Only Database Query)

1. The live default and group values of the twelve keys in section 7.1 (`workspace.prompts`,
   `workspace.prompts_import`, `workspace.prompts_export`, `workspace.skills`, `workspace.skills_import`,
   `workspace.skills_export`, `sharing.prompts`, `sharing.public_prompts`, `sharing.skills`,
   `sharing.public_skills`, `access_grants.allow_users`, `access_grants.allow_groups`) (sections 3.1, 7.1,
   11.5, 11.6).
2. The live values of `ui.enable_community_sharing`, `ui.prompt_suggestions` and `events.webhooks`, and
   which event functions are installed and active, since they receive prompt and skill events with the
   actor's name and email (sections 7.1, 9.1).
3. Counts, as aggregates only: prompts, versions and skills; how many prompts and skills are **Public**;
   how many prompts became Public when the sharing table was introduced (section 6.5); how many prompts and
   skills belong to accounts that no longer exist (section 6.7); how many prompts are switched off but still
   hold a command (section 5.3).
4. Whether any workspace model lists default skills that are not shared with the people who use the model,
   or stale ids of deleted skills (sections 5.23, 5.24).
5. Which production models run with built-in tools on (native Function Calling and the **Builtin Tools**
   capability), since that decides how skills are delivered (section 5.26).
6. Whether prompt texts or skill instructions hold personal or health information. This is a question for
   the data owners; tier 1 and researchers must not read the content (`CLAUDE.md`, `backend/data/`).

### 14.2 Deployment Environment (Answered by the Platform Maintainer)

1. The production host name (section 2).
2. The live values of `BYPASS_ADMIN_ACCESS_CONTROL` (default on), `ENABLE_PLUGINS` and the terminal
   timeout settings (section 7.2).
3. Whether database backups exist, how long they are kept and whether a single deleted prompt or skill can
   be restored from them (sections 5.13, 5.23, 11.21).
4. Whether Open Terminal servers are configured for MedIT GPT, which decides whether terminal skills and
   `/skills:create` are available at all (sections 5.25 to 5.27).

### 14.3 People and Process (Answered by the Service Owner)

1. Whether staff may use the openwebui.com community features: **Share** sends the prompt, including the
   owner's name, email address and sharing entries, to an outside site, and **Discover a prompt** links to
   it (section 5.12). If not, whether **Community Sharing** should be off.
2. Who decides when a command or skill name is held by someone else's prompt or skill, including ones left
   by deleted accounts (sections 11.2, 11.15).
3. The internal escalation route for a suspected privacy incident involving prompts (section 11.19), and the
   support contacts and hours in general (document 02).
4. Whether there are naming conventions for commands and skill IDs (for example department prefixes); none
   exist in code.
5. Whether the history list's inclusion of every author's email address (section 6.2) and the actor details
   in event payloads (section 9.1) are acceptable, or need a note in privacy guidance.
6. **Skills Access** carries the upstream warning `Warning: Enabling this will allow users to upload arbitrary code on the server.`
   (section 10.7). What this permission allows on MedIT GPT is security-sensitive: refer to the platform
   maintainer and U of T Information Security (security.utoronto.ca).

### 14.4 Product Behaviour (Answered by the Platform Maintainer or Upstream Open WebUI)

Each item was read from code and should be confirmed in a test environment before tier 1 relies on it.

1. **`/` skill picks.** In the chat composer a skill chosen from the `/` list is inserted as an `@` chip
   (`<@{id}|{name}>`) that the server does not treat as a skill mention, unlike a `$` pick (sections 1, 4.4,
   5.25; corrected passages). Confirm, and whether upstream treats it as a bug.
2. **Model default skills** are added by the server on every message even after the person switches them
   off in the Integrations menu (sections 5.24, 11.14).
3. **Native mode lists every readable active skill**, not only the switched-on ones (section 5.26; matches
   `builtin-native-tools.md`).
4. **Earlier `$` mentions** keep a skill's full instructions in every later message of the chat (section
   5.25).
5. **Admins and skills.** Skills in an admin's chats follow the admin's own access (no admin bypass), while
   `view_skill` lets an admin load any active skill by id (section 3.2).
6. **Save side effects.** Every prompt content save creates a version even without changes, re-applies the
   sharing with the saver's permissions and moves the prompt to the top of the list (section 5.5); every
   skill save re-applies sharing and writes back the on/off state the editor loaded (section 5.19).
7. **Silent switches.** A refused prompt or skill switch shows no message and the wrong position until a
   reload (sections 5.8, 5.21, 11.11).
8. **Prompt import** of a file that is not JSON, or not a list, does nothing visible (section 5.11).
9. **Version comparison.** `GET /api/v1/prompts/id/{prompt_id}/history/diff` is declared after
   `GET /api/v1/prompts/id/{prompt_id}/history/{history_id}`, so the word `diff` is taken as a version id
   and the request answers `We could not find what you're looking for :/`; no screen calls it
   (`backend/open_webui/routers/prompts.py:638-678`, `:731-772`; sections 2.3, 5.6).
10. **The `/` pop-up** opens only at the start of the message or after a space (the editor library's
    default), and Enter does nothing while a `/word` matches nothing (section 5.14).
11. **Channels.** Choosing a prompt from `/` in a channel inserts a `$command` chip instead of the text
    (section 11.20); how skill chips behave in channel replies was not traced (channels area).
12. **`[object Object]`.** A failed load of the prompt or skill list, and a skill import entry missing
    required fields, show `[object Object]` (sections 5.18, 10).
13. **Create skill entry.** Whether the chat has content is captured when the message box is first shown
    (`src/lib/components/chat/MessageInput.svelte:178-183`, `:1471`), so **Create skill** may be missing
    from `/` in a chat that gained content later until the page is reloaded (section 11.18).
14. **Skill placeholders.** `{{USER_NAME}}` and similar text inside a skill reaches the model unfilled
    (section 5.26).
15. **Skill import sharing.** A JSON skill import keeps the sharing entries from the file, filtered by the
    importer's permissions (section 5.18).
16. **Inactive skills in `$` and `/`.** They are still offered, and choosing one leaves the chip text in the
    message (section 5.21).
17. The upstream **Community Sharing** description mentions only chats although the switch also controls
    prompt sharing and discovery (section 7.1).
18. `src/lib/components/chat/MessageInput/Commands/Prompts.svelte` is not imported anywhere in this release
    (section 13.1).

### 14.5 Knowledgebase Consistency (Answered by the Knowledgebase Maintainer)

1. `chat-composer-and-message-display.md` (section 5.8) says choosing a skill from `/` "adds a skill
   mention"; this document's corrected passages (sections 1, 4.4 and 5.25) say the server does not
   recognize it. Align both after item 14.4.1 is tested.
2. Two passages written earlier in this document were corrected in place on 2026-10-09 (section 1, the
   ways a skill reaches the model; section 4.4, **Skill mention**); they need logging in
   `knowledgebase/tools/VERIFICATION.md`, which this researcher may not edit.
3. Sections 8 and 9 point to `automations-calendar-and-timers.md` and to the events and webhooks material
   of the notifications area, which were not yet written when this was researched; check the references
   once they exist.
4. `workspace-tools-tool-servers-mcp-and-terminals.md` defers terminal skills to "another area"; this
   document covers them only briefly (sections 5.25 to 5.27). Decide whether terminal skills need more depth
   in either document.
5. No contradiction with `knowledgebase/tools/ground-truth.md` was found.
