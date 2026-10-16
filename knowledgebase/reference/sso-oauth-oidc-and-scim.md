# Single Sign-On (OAuth and OIDC), Trusted Headers and SCIM

## At a Glance

- **What the code offers.** Five single sign-on (SSO) providers: `google`, `microsoft`, `github`,
  `oidc` (any OpenID Connect provider; its button label comes from `OAUTH_PROVIDER_NAME`, code
  default `SSO`) and `feishu`. Each is registered once, at start-up, from environment variables, and
  only when its client ID (and secret, or for `oidc` a secret or PKCE) is set
  (`backend/open_webui/config.py:2653-2782`). The code also offers sign-in through a reverse proxy
  that passes the person's email in a **trusted header**, **SCIM 2.0** provisioning, **OIDC
  back-channel logout** and **token exchange** for programs; the last three are off by default
  (`backend/open_webui/env.py:883`, `:901`, `:907`). Which of these production uses, and which
  identity provider sits behind them, is **TO BE CONFIRMED**. The code contains no SAML support and
  no reference to UTORid, Shibboleth or `utoronto` (section 4).
- **The round trip.** A **Continue with …** button on `/auth` sends the browser to
  `/oauth/{provider}/login`, then to the identity provider, back to
  `/oauth/{provider}/login/callback`, and finally to `/auth`, where a session cookie signs the
  person in and `You're now logged in.` appears (`src/routes/auth/+page.svelte:127-152`;
  `backend/open_webui/utils/oauth.py:1850-2260`). Any failure returns to `/auth?error=<text>` and
  the text appears as a red pop-up (`backend/open_webui/utils/oauth.py:2175-2181`;
  `src/routes/auth/+page.svelte:168-171`).
- **Several SSO failures show the password message.** A failed code exchange (including a
  cancelled sign-in at the provider), missing user data, a missing subject or email claim, and an
  email domain outside the allowed list all show
  `The email or password provided is incorrect. Please check for typos and try logging in again.`
  although no password was typed (`backend/open_webui/utils/oauth.py:1889-2008`). The real reason
  is only in the server log (section 10.3).
- **Matching and new accounts.** A returning person is found by provider plus the provider's
  subject identifier. **Merge Accounts by Email** (off by default) links an SSO sign-in to an
  existing account with the same email. **OAuth Signup** (off by default, and separate from the
  ordinary **New Sign Ups** switch) creates accounts; otherwise an unknown person sees
  `You do not have permission to access this resource. Please contact your administrator for assistance.`
  (`backend/open_webui/utils/oauth.py:2010-2152`; `backend/open_webui/config.py:2483`, `:2490`).
- **Role mapping** (off by default) sets the role from a roles claim at every SSO sign-in: an
  admin role gives `admin`, an allowed role gives `user`, and a claim matching neither refuses
  sign-in. An admin whose claim carries only an allowed role is **demoted to `user`** at the next
  sign-in, and a person an admin set to `pending` is restored to `user` whenever the claim matches
  an allowed role (`backend/open_webui/utils/oauth.py:1531-1617`).
- **Group mapping** (off by default) **replaces** a person's group memberships with the groups named
  in the claim at every SSO sign-in, matching groups by name; groups matching **Blocked Groups** are
  left alone, and an empty or missing claim changes nothing. It can also create missing groups, and
  whenever it adds or removes someone it copies the current default permissions onto that group if
  the group's own permissions are empty (`backend/open_webui/utils/oauth.py:1647-1800`).
- **Where settings come from.** The `oauth.*` settings follow the environment on every start unless
  `ENABLE_OAUTH_PERSISTENT_CONFIG=True` (code default `False`); while they follow the environment the
  admin **OAuth / OIDC** section is read-only (`backend/open_webui/models/config.py:133-138`;
  `src/lib/components/admin/Settings/Authentication.svelte:550-564`). Provider credentials, URLs,
  scopes and the button label are read from the environment at start-up even when the setting is
  persistent (section 7.3).
- **Sessions.** An SSO sign-in produces the same MedIT GPT session token as a password sign-in,
  lasting `auth.jwt_expiry` (code default four weeks) regardless of the provider's own session
  (`backend/open_webui/utils/oauth.py:2154-2198`). Sign-out can send the browser to the provider's
  sign-out page (`backend/open_webui/routers/auths.py:994-1047`). Back-channel logout ends existing
  MedIT GPT sessions only when Redis is configured (`backend/open_webui/utils/oauth.py:2418-2434`).
- **Trusted headers** sign people in automatically, create unknown accounts even with sign-up off,
  and can set groups and the role from further headers at each sign-in
  (`backend/open_webui/routers/auths.py:732-786`).
- **SCIM** (`/api/v1/scim/v2`, off by default) creates, updates, suspends and deletes accounts and
  groups from an identity provider. SCIM-created accounts have no password record, so they can sign
  in only through SSO, and only once **Merge Accounts by Email** links them
  (`backend/open_webui/routers/scim.py:573-656`; `backend/open_webui/utils/oauth.py:2010-2019`).
- **Tool-server OAuth is separate.** MCP tool servers can require each person to connect their own
  account at another service; the chat shows the tool in amber with **Click to connect**
  (`src/lib/components/chat/MessageInput.svelte:2546-2559`). Depth is in
  `workspace-tools-tool-servers-mcp-and-terminals.md`.
- **Local customisation.** None in this area's logic; it matches upstream Open WebUI v0.11.4
  apart from the product name (section 12).

## 1. Purpose and Who Uses It

This area covers every way a person's identity can come from **outside** MedIT GPT:

- signing in with an external identity provider over OAuth 2.0 or OpenID Connect (OIDC), the
  **Continue with …** buttons on the sign-in page;
- how such a sign-in finds, links or creates the MedIT GPT account, and how it can change the
  account's role, groups, name, email and picture each time;
- signing in through a reverse proxy that has already identified the person and passes their email
  in a **trusted header**;
- **SCIM 2.0** provisioning, where an identity provider creates, updates, suspends and deletes
  accounts and groups directly;
- signing out of the identity provider as well as MedIT GPT, and **back-channel logout**, where the
  identity provider tells MedIT GPT that a person signed out;
- **token exchange**, where a program swaps an identity-provider token for a MedIT GPT session; and
- from a user's point of view only, the per-person OAuth connections that MCP tool servers use.

**Who uses it.**

| Who | What they do here | Evidence |
|---|---|---|
| Every person | Chooses a **Continue with …** button, or is forwarded to the provider automatically; signs out | `src/routes/auth/+page.svelte:176-195`, `:451-587`; `src/lib/components/layout/Sidebar/UserMenu.svelte:579-594` |
| A new person | Gets an account on first SSO sign-in when **OAuth Signup** is on, or on first trusted-header sign-in | `backend/open_webui/utils/oauth.py:2093-2152`; `backend/open_webui/routers/auths.py:747-759` |
| A person using MCP tools | Connects, and later disconnects, their own account at a tool server's sign-in service | `src/lib/components/chat/MessageInput.svelte:2546-2559`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:593-618` |
| An admin | Reads (or, with persistent OAuth settings, edits) the **OAuth / OIDC** section of the **Authentication** settings; sees each account's **OAuth ID** in the user editor | `src/lib/components/admin/Settings/Authentication.svelte:546-876`; `src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198` |
| The operator (server environment) | Registers providers, sets claims, domains, role and group mapping, trusted headers, SCIM, back-channel logout and token exchange through environment variables | `backend/open_webui/config.py:2478-2782`; `backend/open_webui/env.py:802-916` |
| The identity provider | Receives the sign-in request, sends the person back, calls back-channel logout, and acts as the SCIM client | `backend/open_webui/main.py:2828-2865`; `backend/open_webui/routers/scim.py:232-290` |
| An external program | Exchanges an identity-provider token for a MedIT GPT session, when allowed | `backend/open_webui/routers/auths.py:1624-1771` |
| Tier 1 support | Reads symptoms and messages, checks settings with an admin, escalates | Sections 10 and 11 |

**Not covered here** (cross-referenced by file name):

- The sign-in page as a whole, password sign-in, sign-up, pending accounts, session tokens and their
  expiry, sign-out basics, API keys and LDAP: `authentication-and-sign-in.md`.
- Roles, groups, permission keys, approving `pending` users and deleting users:
  `users-groups-roles-and-permissions.md`.
- Tool servers, MCP, their OAuth registration and the admin side of connecting them:
  `workspace-tools-tool-servers-mcp-and-terminals.md`.
- The full catalogue of `oauth.*` keys and other persistent settings:
  `configuration-persistent-settings-a-to-o.md`.
- Every other admin settings panel: `admin-settings-panels.md`.
- Model connections whose authentication type is **OAuth** or **Entra ID**:
  `model-connections-openai-ollama-and-direct.md`.

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; every path below is relative to the site root. The
identity provider's own pages are outside MedIT GPT, and which provider production uses is
**TO BE CONFIRMED**.

### 2.1 Screens

| Screen | How a person reaches it | Who sees it | Source |
|---|---|---|---|
| SSO buttons on the sign-in page | `/auth`. One **Continue with …** button per registered provider, below the email form with an `or` divider when the form is shown | Anyone not signed in, when at least one provider is registered and **OAuth / OIDC** is on | `src/routes/auth/+page.svelte:451-587`; `backend/open_webui/main.py:2317-2326` |
| Automatic forwarding to the provider | Opening `/auth` (including the `/auth?redirect=<page>` the app sends signed-out people to) when **Auto Redirect** is on and SSO is the only way in (section 5.1) | Anyone not signed in | `src/routes/auth/+page.svelte:176-195`; `src/routes/(app)/+layout.svelte:197-216` |
| The identity provider's sign-in and consent pages | After choosing a button | Anyone signing in by SSO | `backend/open_webui/utils/oauth.py:1850-1870` |
| Sign-in page with an error pop-up | `/auth?error=<text>` after a failed SSO round trip | The person whose sign-in failed | `backend/open_webui/utils/oauth.py:2175-2181`; `src/routes/auth/+page.svelte:168-171` |
| "Signing in to MedIT GPT" screen | `/auth` in trusted-header mode: a spinner while the page signs in automatically | Everyone, when trusted headers are configured | `src/routes/auth/+page.svelte:199-200`, `:235-248` |
| The provider's sign-out page | After **Sign Out**, when the server returns the provider's end-session address | People signed in by SSO | `backend/open_webui/routers/auths.py:994-1047`; `src/lib/apis/auths/index.ts:410-438` |
| **Settings → Admin → Authentication → OAuth / OIDC** | In the **Settings** window's **Admin** list (deep link `/admin/settings/authentication`); the section appears below LDAP | `admin` only | `src/lib/components/admin/Settings/Authentication.svelte:546-876`; navigation in `authentication-and-sign-in.md` |
| **OAuth ID** in the admin user editor | Admin user list → edit a person; shows each provider name and subject identifier linked to the account | `admin` only | `src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198`; navigation in `users-groups-roles-and-permissions.md` |
| Amber tool chips in the chat composer | A model's default MCP tool that needs the person to connect; hover text **Click to connect** | Signed-in people using such tools | `src/lib/components/chat/MessageInput.svelte:2546-2559`; `src/lib/components/chat/Chat.svelte:1038-1055` |
| **Disconnect OAuth** in the integrations menu | The tools list in the chat composer's integrations menu, beside a connected MCP tool server | Signed-in people | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:593-618` |
| Home page with an error pop-up | `/?error=<text>` after a failed tool-server connection | The person who tried to connect | `backend/open_webui/utils/oauth.py:1318-1324`; `src/routes/(app)/+page.svelte:8-12` |

### 2.2 Server Endpoints

Useful when reading server logs or a browser's developer tools.

| Method and path | Purpose | Called by | Source |
|---|---|---|---|
| `GET /oauth/{provider}/login` | Starts an SSO sign-in; `{provider}` is `google`, `microsoft`, `github`, `oidc` or `feishu`. Answers 404 when **OAuth / OIDC** is off or the provider is not registered | The browser, from a button or auto redirect | `backend/open_webui/main.py:2828-2830`; `backend/open_webui/utils/oauth.py:1850-1870` |
| `GET /oauth/{provider}/login/callback` (also the older `GET /oauth/{provider}/callback`) | Where the provider sends the person back; finishes the sign-in and redirects to `/auth` | The browser, sent by the provider | `backend/open_webui/main.py:2833-2850`; `backend/open_webui/utils/oauth.py:1872-2260` |
| `POST /oauth/backchannel-logout` | The provider reports that a person signed out. Answers 404 unless `ENABLE_OAUTH_BACKCHANNEL_LOGOUT=True` | The identity provider | `backend/open_webui/main.py:2858-2865`; `backend/open_webui/utils/oauth.py:2262-2447` |
| `GET /oauth/clients/{client_id}/authorize` | Starts a tool-server connection (`client_id` looks like `mcp:<server id>`) | A signed-in `user` or `admin`, through the browser | `backend/open_webui/main.py:2772-2812` |
| `GET /oauth/clients/{client_id}/callback` | Where the tool server's sign-in service sends the person back; redirects to `/` | The browser | `backend/open_webui/main.py:2815-2825`; `backend/open_webui/utils/oauth.py:1234-1327` |
| `GET /api/config` | Tells the sign-in page which providers to show (`oauth.providers`), whether to auto-redirect (`oauth.auto_redirect`) and whether trusted headers are on (`features.auth_trusted_header`) | Anyone | `backend/open_webui/main.py:2317-2331` |
| `POST /api/v1/auths/signin` | Also the trusted-header sign-in: the server reads the proxy's headers instead of the form | The sign-in page | `backend/open_webui/routers/auths.py:717-786` |
| `POST /api/v1/auths/signout` | Signs out; for SSO sessions may return the provider's sign-out address | Any signed-in person | `backend/open_webui/routers/auths.py:955-1059` |
| `GET`, `POST /api/v1/auths/admin/config/oauth` | Reads or saves the **OAuth / OIDC** settings | `admin` | `backend/open_webui/routers/auths.py:1506-1514` |
| `DELETE /api/v1/auths/oauth/sessions/{provider}` | Disconnects the caller's own tool-server connection (`provider` such as `mcp:<server id>`) | `user` or `admin` | `backend/open_webui/routers/auths.py:1067-1093` |
| `POST /api/v1/auths/oauth/{provider}/token/exchange` | Swaps an identity-provider access token for a MedIT GPT session; 403 unless `ENABLE_OAUTH_TOKEN_EXCHANGE=True` | External programs | `backend/open_webui/routers/auths.py:1624-1771` |
| `POST /api/v1/configs/oauth/clients/register` | Registers a tool server's OAuth client (admin side; detail in the tools document) | `admin` | `backend/open_webui/routers/configs.py:172-209` |
| `/api/v1/scim/v2/Users`, `/api/v1/scim/v2/Users/{user_id}` | SCIM user list (filters `userName eq` and `externalId eq`), read, create, replace, patch and delete | The identity provider's SCIM client, with the SCIM bearer token | `backend/open_webui/routers/scim.py:498-872` |
| `/api/v1/scim/v2/Groups`, `/api/v1/scim/v2/Groups/{group_id}` | SCIM group list (filter `displayName eq`), read, create, replace, patch and delete | The identity provider's SCIM client, with the SCIM bearer token | `backend/open_webui/routers/scim.py:876-1200` |
| `/api/v1/scim/v2/ServiceProviderConfig`, `/ResourceTypes`, `/Schemas` | SCIM discovery: what this server supports (patch and filter yes; bulk, sort, password change and ETags no) | The identity provider's SCIM client | `backend/open_webui/routers/scim.py:400-494` |

The SCIM paths exist only when `ENABLE_SCIM` (or the older `SCIM_ENABLED`) is `True` at start-up
(`backend/open_webui/main.py:885-887`; `backend/open_webui/env.py:907`).

## 3. Roles and Permissions

The three roles are `admin`, `user` and `pending` (ground truth); approving and changing roles by
hand is in `users-groups-roles-and-permissions.md`. This section covers how the identity paths in
this area **set** roles, which is where most surprises come from.

### 3.1 Who May Do What

| Action | `pending` | `user` | `admin` | Source |
|---|---|---|---|---|
| Sign in by SSO or trusted header | Yes (then sees the Account Activation Pending overlay) | Yes | Yes | No role check in `backend/open_webui/utils/oauth.py:1872-2260` or `backend/open_webui/routers/auths.py:732-786` |
| Connect or disconnect a tool server's OAuth sign-in | No | Yes | Yes | `backend/open_webui/main.py:2772-2778` (`get_verified_user`); `backend/open_webui/routers/auths.py:1067-1073` |
| Read the **OAuth / OIDC** settings | No | No | Yes | `backend/open_webui/routers/auths.py:1506-1508` (`get_admin_user`) |
| Edit the **OAuth / OIDC** settings | No | No | Yes, only when `ENABLE_OAUTH_PERSISTENT_CONFIG=True` | `backend/open_webui/routers/auths.py:1511-1514`; `src/lib/components/admin/Settings/Authentication.svelte:52`, `:561-564` |
| See an account's **OAuth ID** | No | No | Yes | `src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198` |
| Provision accounts and groups by SCIM | Not a MedIT GPT role: the identity provider's SCIM client, holding the SCIM bearer token | | | `backend/open_webui/routers/scim.py:232-290` |
| Report a sign-out by back-channel logout | Not a MedIT GPT role: a configured identity provider | | | `backend/open_webui/utils/oauth.py:2284-2331` |

### 3.2 How Each Path Decides the Role

| Path and setting | New account | Existing account | Source |
|---|---|---|---|
| SSO, **Role Mapping** off (code default) | `ui.default_user_role` (code default `pending`); the very first account in the installation becomes `admin` | Keeps its current role | `backend/open_webui/utils/oauth.py:1609-1615`, `:2122`, `:2133-2135`; `backend/open_webui/config.py:2580` |
| SSO, **Role Mapping** on, roles claim present | `admin` if the claim holds any **Admin Roles** value; otherwise `user` if it holds any **Allowed Roles** value, or if **Allowed Roles** contains `*`; otherwise sign-in is refused | Same rule, applied at every sign-in, so the role can go up or down | `backend/open_webui/utils/oauth.py:1546-1608` |
| SSO, **Role Mapping** on, roles claim missing or empty | `ui.default_user_role` | Keeps its current role | `backend/open_webui/utils/oauth.py:1552-1553`, `:1586` |
| SSO, the account is the only account in the installation | Not applicable | Set to `admin` at every SSO sign-in | `backend/open_webui/utils/oauth.py:1533-1537` |
| Trusted header | `ui.default_user_role`; the very first account becomes `admin` and **New Sign Ups** is switched off | Unchanged, unless a role header is configured | `backend/open_webui/routers/auths.py:841-879` |
| Trusted header with `WEBUI_AUTH_TRUSTED_ROLE_HEADER` | The header's value is applied straight after creation | Set to the header's value (`admin`, `user` or `pending`, any letter case) at every sign-in; other values are ignored and logged | `backend/open_webui/routers/auths.py:770-786` |
| SCIM create | `user` when the request says `active: true` (the default), `pending` when `active: false`. The default user role and default group are not used | Not applicable | `backend/open_webui/routers/scim.py:622-629` |
| SCIM update (`PUT` or `PATCH` of `active`) | Not applicable | `user` for `active: true`, `pending` for `active: false`; an existing `admin` is never changed by this flag | `backend/open_webui/routers/scim.py:692-696`, `:783-788` |
| Token exchange | Not applicable (the account must already exist) | Same rule as SSO with role mapping; in addition, with role mapping on, no readable roles claim and no `*` in **Allowed Roles**, the exchange is refused | `backend/open_webui/utils/oauth.py:1576-1578`; `backend/open_webui/routers/auths.py:1754-1761` |

The code defaults are **Roles Claim** `roles`, **Allowed Roles** `user` and `admin`, and **Admin
Roles** `admin` (`backend/open_webui/config.py:2595-2607`). The claim may be a list, a single value,
a number, or text split by `OAUTH_ROLES_SEPARATOR` (code default `,`), and a dotted claim name such
as `realm_access.roles` reads a nested value (`backend/open_webui/utils/oauth.py:191-198`,
`:1565-1574`). Role values are compared exactly, letter case included
(`backend/open_webui/utils/oauth.py:1588-1599`).

### 3.3 Consequences of Role Mapping That Support Will See

- **Admins can be demoted by their own sign-in.** An `admin` whose claim carries an allowed role but
  no admin role becomes `user` at the next SSO sign-in (`backend/open_webui/utils/oauth.py:1586-1599`,
  `:1629-1635`). The code makes no exception for the primary (earliest) admin, which the admin user
  list otherwise protects (`users-groups-roles-and-permissions.md`).
- **Manual role changes do not stick.** With role mapping on and a matching claim, a role an admin
  set by hand (including `pending` used as a suspension) is replaced at the person's next SSO
  sign-in.
- **A claim that matches nothing refuses sign-in**, with
  `You do not have permission to access this resource. Please contact your administrator for assistance.`
  on the sign-in page, and the log line in section 10.3 names the roles that were received
  (`backend/open_webui/utils/oauth.py:1600-1608`).
- **A role change disconnects the person's open tabs.** Every role change publishes
  `user.role_updated`, and that event disconnects the person's live connections, so other open tabs
  briefly show `Connection lost. Reconnecting...` (`backend/open_webui/utils/oauth.py:1636-1643`;
  `backend/open_webui/events.py:1087-1098`; `backend/open_webui/socket/main.py:388-403`;
  `src/routes/+layout.svelte:162`).

### 3.4 Permissions

No SSO, trusted-header or SCIM step checks a permission key. They change permissions indirectly by
changing group memberships, because a person's permissions add up across their groups (ground
truth). Group mapping is in section 5.6; the permission model is in
`users-groups-roles-and-permissions.md`.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| Identity provider | The outside service that checks who a person is (for example a university directory service). MedIT GPT never sees the person's provider password | `backend/open_webui/utils/oauth.py:1850-1870` |
| OAuth 2.0 and OpenID Connect (OIDC) | The standard protocols the SSO buttons use. OIDC adds a signed identity statement and a **discovery document** (a `.well-known/openid-configuration` address) listing the provider's endpoints | `backend/open_webui/config.py:2653-2759` |
| Provider (in MedIT GPT) | One of five fixed names: `google`, `microsoft`, `github`, `oidc`, `feishu`. Each is registered at start-up only if its environment variables are set; there is at most one `oidc` provider | `backend/open_webui/config.py:2653-2759`, `:2782` |
| Client ID and client secret | The identifiers the identity provider issued for MedIT GPT. They are credentials: never copy them into a ticket | `backend/open_webui/config.py:2494-2543` |
| Redirect URI (callback) | The MedIT GPT address the provider sends people back to: `/oauth/{provider}/login/callback`. It must be registered at the provider. Unless the provider's redirect variable is set, the server builds it from the address the request arrived on | `backend/open_webui/utils/oauth.py:1860-1862`; `backend/open_webui/main.py:2833-2834` |
| Scopes | What MedIT GPT asks the provider for; code defaults `openid email profile` (Google, Microsoft, OIDC), `user:email` (GitHub), `contact:user.base:readonly` (Feishu) | `backend/open_webui/config.py:2499`, `:2529`, `:2537`, `:2551`, `:2576` |
| Claim | A named value in the provider's answer about the person. The code reads the email (`email`), display name (`name`), picture (`picture`), subject (`sub`), roles (`roles`) and groups (`groups`) claims; every name is configurable | `backend/open_webui/config.py:2561-2570`, `:2595` |
| Subject identifier | The provider's permanent identifier for the person. GitHub uses `id` and Feishu `user_id` unless `OAUTH_SUB_CLAIM` says otherwise | `backend/open_webui/utils/oauth.py:1945-1954`; `backend/open_webui/config.py:2709`, `:2758` |
| Account link (**OAuth ID**) | The `user.oauth` value `{provider: {"sub": "<subject>"}}`. A returning person is found through it; admins see it as **OAuth ID** | `backend/open_webui/models/users.py:172`, `:455-473`, `:777-792`; `src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198` |
| Merge by email | **Merge Accounts by Email**: when no account carries the subject, link the sign-in to an account with the same email instead (off by default) | `backend/open_webui/utils/oauth.py:2012-2019`; `backend/open_webui/config.py:2490` |
| OAuth sign-up | **OAuth Signup**: create an account for an unknown person at first SSO sign-in (off by default). Separate from **New Sign Ups**, which governs only the email form | `backend/open_webui/utils/oauth.py:2093-2152`; `backend/open_webui/config.py:2483` |
| Allowed domains | The email domains allowed to sign in by SSO, code default `*` (any) | `backend/open_webui/utils/oauth.py:2002-2008`; `backend/open_webui/config.py:2609` |
| Role mapping, group mapping | Setting the role, and replacing group memberships, from claims at each SSO sign-in (sections 3.2 and 5.6) | `backend/open_webui/utils/oauth.py:1531-1800` |
| Blocked groups | Group names or patterns that group mapping never adds a person to or removes them from. Despite the admin screen's description, they do not block sign-in | `backend/open_webui/utils/oauth.py:313-364`, `:1730-1771`; `src/lib/i18n/locales/en-US/translation.json:2048` |
| Persistent OAuth configuration | `ENABLE_OAUTH_PERSISTENT_CONFIG`. Off (code default): every `oauth.*` setting is re-read from the environment at each start and the admin section is read-only. On: the settings are stored in the database and editable | `backend/open_webui/config.py:3232-3238`; `backend/open_webui/models/config.py:133-138` |
| MedIT GPT session token | The token SSO issues after a successful round trip; the same kind, and the same lifetime (`auth.jwt_expiry`), as a password sign-in. Detail in `authentication-and-sign-in.md` | `backend/open_webui/utils/oauth.py:2154-2157` |
| Stored SSO session | A server-side `oauth_session` record holding the provider's tokens for one sign-in on one device, named by the `oauth_session_id` cookie. Used for provider sign-out and for features that forward the person's provider token | `backend/open_webui/models/oauth_sessions.py:23-39`; `backend/open_webui/utils/oauth.py:2221-2258` |
| End-session (provider sign-out) | The provider's sign-out address, which MedIT GPT can send the browser to after **Sign Out** | `backend/open_webui/routers/auths.py:994-1047` |
| Back-channel logout | A server-to-server message from the provider saying a person signed out, so MedIT GPT can end their sessions | `backend/open_webui/utils/oauth.py:2262-2447` |
| Trusted header | Sign-in by a reverse proxy that has already identified the person and passes their email (and optionally name, groups and role) in request headers | `backend/open_webui/env.py:802-805`; `backend/open_webui/routers/auths.py:732-786` |
| SCIM | System for Cross-domain Identity Management: a standard API an identity provider uses to create, update and remove accounts and groups. The code calls its implementation experimental | `backend/open_webui/routers/scim.py:1-6` |
| SCIM external ID | The identity provider's own identifier for a SCIM account, kept in `user.scim` under the provider named by `SCIM_AUTH_PROVIDER` | `backend/open_webui/models/users.py:173`, `:794-812`; `backend/open_webui/env.py:909` |
| Token exchange | A program presents an identity-provider access token and receives a MedIT GPT session for the matching account (off by default) | `backend/open_webui/routers/auths.py:1624-1771` |
| Tool-server OAuth | A separate, per-person sign-in to an MCP tool server's own authorization service (types **OAuth 2.1**, with automatic client registration, and **OAuth 2.1 (Static)**). Unrelated to the SSO buttons except for the shared session table | `backend/open_webui/utils/oauth.py:829-1327`; `src/lib/components/AddToolServerModal.svelte:762-765` |
| **OAuth** authentication type for connections | A model connection, tool server or terminal set to **OAuth** forwards the signed-in person's SSO access token: "Forwards system user OAuth access token to authenticate" | `backend/open_webui/routers/openai.py:194-205`; `backend/open_webui/utils/tools.py:154-157`; `src/lib/components/AddConnectionModal.svelte:428`, `:450-452` |
| PKCE | An extra safeguard on the code exchange. `OAUTH_CODE_CHALLENGE_METHOD=S256` enables it for the Google, Microsoft, GitHub and OIDC registrations and lets `oidc` work without a client secret; any other non-empty value raises an error while those providers are registered at start-up | `backend/open_webui/config.py:2636-2650`, `:2712`; `backend/open_webui/utils/oauth.py:1337-1343` |
| Auto redirect | **Auto Redirect**: the sign-in page forwards straight to the only provider when SSO is the only way in (section 5.1) | `src/routes/auth/+page.svelte:176-195` |

**UTORid and Microsoft Entra ID.** A search of `backend/open_webui` and `src` finds no reference to
UTORid, Shibboleth, SAML or `utoronto`; SSO in this code is OAuth 2.0 and OIDC only. The
`microsoft` provider signs in against `MICROSOFT_CLIENT_LOGIN_BASE_URL` (code default
`https://login.microsoftonline.com`) for one tenant named by `MICROSOFT_CLIENT_TENANT_ID`
(`backend/open_webui/config.py:2515-2531`, `:2673-2689`), and a code comment names "Microsoft Entra
ID" as a provider whose ID token carries roles and groups that the code keeps
(`backend/open_webui/utils/oauth.py:1924-1926`). A UTORid sign-in could reach MedIT GPT only through
one of the paths the code offers (the `microsoft` provider, the generic `oidc` provider, or a
reverse proxy using trusted headers); **which, if any, production uses, and the identity provider
behind it, is TO BE CONFIRMED.** The **Entra ID** authentication type offered for model connections
uses the server's own Azure credential for Azure OpenAI and has nothing to do with people signing
in (`backend/open_webui/routers/openai.py:208-209`, `:221-232`;
`src/lib/components/AddConnectionModal.svelte:429`).

## 5. Workflows (Step by Step)

### 5.1 How the Sign-In Page Offers SSO

1. Before anyone signs in, the browser reads `GET /api/config`. Its `oauth.providers` field lists
   every registered provider with its display name (for `oidc`, the value of
   `OAUTH_PROVIDER_NAME`), and is empty while **OAuth / OIDC** (`oauth.enable`, code default on) is
   off; `oauth.auto_redirect` carries **Auto Redirect** (`backend/open_webui/main.py:2317-2326`).
2. `/auth` shows one button per listed provider, in this order, each labelled
   `Continue with {{provider}}`: Google, Microsoft, GitHub, the OIDC provider (its display name, or
   `SSO` if none), Feishu (`src/routes/auth/+page.svelte:451-587`). A line with `or` separates the
   buttons from the email or LDAP form when either form is shown (`src/routes/auth/+page.svelte:454-459`).
   Choosing a button sends the browser to `/oauth/{provider}/login`.
3. **Auto Redirect.** When **Auto Redirect** is on, the page skips the buttons and forwards
   straight to the provider. Among the conditions the code checks: exactly one provider is listed;
   the login form, LDAP and trusted headers are all off; no-login mode is off; the installation is
   past first run; the browser holds no session token (in local storage or the `token` cookie); and
   the address carries neither `state=logout` nor `error` (`src/routes/auth/+page.svelte:176-195`).
   So after **Sign Out** (which lands on `/auth?state=logout`) or after a failed sign-in (which
   lands on `/auth?error=…`), the person sees the sign-in card with the button instead of being
   forwarded again.
4. When the app sends a signed-out person to `/auth?redirect=<page>`, the page remembers that page
   in the browser's local storage (`redirectPath`) so the SSO round trip can return there
   (`src/routes/(app)/+layout.svelte:197-216`; `src/routes/auth/+page.svelte:157-166`, `:151`).

### 5.2 Signing In with an SSO Button, End to End

Each step lists where it can fail and exactly what the person sees. Messages from the callback
reach the person as a red pop-up on `/auth`, because the server redirects to
`/auth?error=<message>` (`backend/open_webui/utils/oauth.py:2175-2181`;
`src/routes/auth/+page.svelte:168-171`).

1. **Start.** The browser opens `/oauth/{provider}/login` (`backend/open_webui/main.py:2828-2830`).
   - **OAuth / OIDC** off, or the provider not registered: a bare page reading
     `{"detail":"Not Found"}` (HTTP 404; the text is the web framework's default for a 404)
     (`backend/open_webui/utils/oauth.py:1851-1859`;
     `.venv/lib/python3.12/site-packages/starlette/exceptions.py:8-10`, local environment, not
     repository code).
   - The provider's discovery document cannot be fetched (provider or network down): the code has
     no handler for this, so the framework's plain `Internal Server Error` page appears (HTTP 500)
     (`backend/open_webui/utils/oauth.py:1870`;
     `.venv/lib/python3.12/site-packages/starlette/middleware/errors.py:259`). Read from the code, not
     exercised.
2. **Request to the provider.** The server chooses the callback address (the provider's redirect
   variable if set, otherwise `/oauth/{provider}/login/callback` on the address the request arrived
   on), adds `audience` from **OAUTH_AUDIENCE** and any extra parameters from
   `OAUTH_AUTHORIZE_PARAMS`, remembers a one-time "state" value in the `owui-session` cookie and
   redirects the browser to the provider (`backend/open_webui/utils/oauth.py:1860-1870`;
   `backend/open_webui/main.py:2649-2674`; `backend/open_webui/config.py:2621-2633`).
3. **At the identity provider.** The person signs in there (and completes any second factor the
   provider requires). Problems at this stage, such as a callback address the provider does not
   recognize or a person not permitted to use the application, appear on the **provider's** pages,
   in the provider's words. What the U of T provider shows is **TO BE CONFIRMED**.
4. **Back at MedIT GPT.** The provider sends the browser to the callback with a one-time code, and
   the server exchanges it for the provider's tokens (`backend/open_webui/utils/oauth.py:1883-1920`).
   If the provider rejected the token's signature, the code refreshes the provider's signing keys
   and tries once more (`:1891-1911`).
   - Any failure here shows
     `The email or password provided is incorrect. Please check for typos and try logging in again.`
     Typical causes: the person cancelled or was refused at the provider (the provider returns an
     error instead of a code); the `owui-session` cookie holding the state was lost or expired, for
     example because the round trip started on a different address or in another browser; the code
     was already used (back button, double click); the client secret is wrong or expired; MedIT
     GPT cannot reach the provider. The server log line
     `OAuth callback error during authorize_access_token for provider {provider}: {detail}` gives
     the real reason (`backend/open_webui/utils/oauth.py:1912-1920`).
5. **Who is this?** The server reads the person's details from the provider's identity statement
   and, when the email or name claim is missing there, also asks the provider's user-information
   endpoint, keeping identity-statement claims (such as roles and groups) that the endpoint does
   not repeat (`backend/open_webui/utils/oauth.py:1922-1940`).
   - No details at all: the password message above (`:1941-1943`).
6. **Subject identifier.** Read from **Sub Claim** if set, otherwise from the provider's usual claim
   (`sub`; `id` for GitHub; `user_id` for Feishu) (`backend/open_webui/utils/oauth.py:1945-1954`).
   - Missing: the password message (`:1951-1953`).
7. **Email.** Read from **Email Claim** (code default `email`) (`backend/open_webui/utils/oauth.py:1961-2001`).
   - Missing, GitHub: the server asks GitHub for the person's primary email; if GitHub has none or
     cannot be reached, the password message (`:1967-1994`).
   - Missing, other providers: the password message, unless `ENABLE_OAUTH_EMAIL_FALLBACK=True`, in
     which case the account gets a made-up address of the form `{provider}@{sub}.local` (`:1995-1999`).
   - The email is lower-cased.
8. **Allowed domain.** Unless **Allowed Domains** contains `*`, the part after `@` must equal one of
   the listed domains exactly. Subdomains are separate entries, and the list itself is not
   lower-cased, so an entry typed with capitals never matches
   (`backend/open_webui/utils/oauth.py:2002-2008`; `backend/open_webui/config.py:2609`;
   `backend/open_webui/routers/auths.py:1475-1477`).
   - Not allowed: the password message.
9. **Find, link or create the account** (section 5.3), then apply role mapping and profile updates
   to an existing account (section 5.4).
   - Role claim matches no allowed or admin role:
     `You do not have permission to access this resource. Please contact your administrator for assistance.`
   - No account and **OAuth Signup** off: the same permission message (`:2148-2152`).
   - No account, **OAuth Signup** on, but the email belongs to an account not linked to this
     subject (and **Merge Accounts by Email** off):
     `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.`
     (`:2095-2099`).
   - The new account could not be stored:
     `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.`
     (`:2127-2128`).
10. **Session token.** The server issues a MedIT GPT session token lasting `auth.jwt_expiry` (code
    default `4w`) (`backend/open_webui/utils/oauth.py:2154-2157`).
11. **Group mapping**, when on (section 5.6) (`backend/open_webui/utils/oauth.py:2158-2165`).
    - Any unexpected error in steps 4 to 11 that is not one of the messages above shows
      `[ERROR: Error during OAuth process]` (`backend/open_webui/utils/oauth.py:2167-2173`;
      `backend/open_webui/constants.py:16-23`). The log line `Error during OAuth process: {e}`
      accompanies every callback failure.
12. **Return to MedIT GPT.** The server redirects to `/auth` on the **WebUI URL** address
    (`webui.url`), or on the address the request arrived on when that setting is empty, and sets
    the cookies in section 5.8. It publishes `auth.login` with source `oauth`. It also stores the
    SSO session record; if that fails, sign-in still succeeds but provider sign-out and token
    forwarding do not work for that sign-in (`backend/open_webui/utils/oauth.py:2175-2258`).
13. **In the browser.** `/auth` finds the `token` cookie, confirms it with `GET /api/v1/auths/`,
    keeps it, shows `You're now logged in.` and opens the remembered page or `/`
    (`src/routes/auth/+page.svelte:127-152`, `:47-71`). If the confirmation fails, the server's
    refusal text appears as a red pop-up and the person stays on `/auth` (`:141-148`). A `pending`
    account then sees the Account Activation Pending overlay (`authentication-and-sign-in.md`).

Two outcomes are read from the code but not exercised, and are recorded in section 14: if
**WebUI URL** names a different address from the one the person used, the cookie set in step 12
may not be visible where the browser lands, and the person sees the sign-in page again without an
error; and if the cookie flags (`WEBUI_SESSION_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE`)
stop the browser returning the `owui-session` cookie on the provider's redirect, step 4 fails with
the password message.

### 5.3 How the Account Is Found, Linked or Created

The server tries, in order (`backend/open_webui/utils/oauth.py:2010-2152`; the order is also stated
in `backend/open_webui/main.py:2841-2849`):

| Situation | **Merge Accounts by Email** off (code default) | **Merge Accounts by Email** on |
|---|---|---|
| An account already carries this provider's subject | Signed in to that account; its email is not compared | Same |
| No account carries the subject, but an account has the same email (any letter case) | **OAuth Signup** on: refused with `Uh-oh! This email is already registered. …`; **OAuth Signup** off: refused with the permission message | The subject is added to that account (its **OAuth ID**) and the person is signed in to it |
| No account at all | **OAuth Signup** on: a new account is created; off: refused with the permission message | Same |

Points to know:

- **The link is per provider.** An account linked to `microsoft` is not found by a `google` sign-in;
  with merge off, the second provider's sign-in is refused as above.
- **Changing the subject breaks every link.** If the provider, tenant or **Sub Claim** changes so
  that subjects differ, existing people stop matching and are refused (or, with merge on, re-linked
  by email). Confirm with the platform maintainer before any such change (TO BE CONFIRMED who
  decides).
- **Merging trusts the provider's email.** The code's own comment warns: "note: some providers do
  not verify email addresses" (`backend/open_webui/main.py:2845-2846`). Security-sensitive: refer to
  the platform maintainer and U of T Information Security (security.utoronto.ca).
- **Linking is how SCIM, password, LDAP and trusted-header accounts first sign in by SSO**: none of
  them carries a subject until merge links it.

**How OAuth sign-up differs from ordinary sign-up** (ordinary sign-up is in
`authentication-and-sign-in.md`):

| Aspect | SSO account creation | Source |
|---|---|---|
| Switch | **OAuth Signup** (`oauth.enable_signup`, code default off); **New Sign Ups** and **Login Form** play no part | `backend/open_webui/utils/oauth.py:2095`; `backend/open_webui/config.py:2483` |
| Password | A random value nobody knows, so the account cannot use email-and-password sign-in | `backend/open_webui/utils/oauth.py:2117-2125` |
| Role | `ui.default_user_role`, or the role-mapping result (section 3.2); the very first account becomes `admin` but, unlike ordinary sign-up, **New Sign Ups** is not switched off | `backend/open_webui/utils/oauth.py:2122`, `:2133-2135`; compare `backend/open_webui/routers/auths.py:876-879` |
| Name | The **Username Claim** value (code default `name`), or the email when it is missing | `backend/open_webui/utils/oauth.py:2110-2115` |
| Picture | The **Picture Claim** value, or the provider's own default picture address (for Microsoft, the Microsoft Graph photo), fetched and stored as an image; `/user.png` when nothing usable is found or the image is not PNG, JPEG, GIF or WebP | `backend/open_webui/utils/oauth.py:2101-2109`, `:1802-1848`; `backend/open_webui/config.py:2523-2526` |
| Email check | No format check; the allowed-domain list applies instead | `backend/open_webui/utils/oauth.py:2001-2008` |
| Default group | Applied, as for other sign-ups | `backend/open_webui/utils/oauth.py:2137-2138` |
| Event | `user.created` with source `oauth` | `backend/open_webui/utils/oauth.py:2139-2146` |

### 5.4 What Changes at Every SSO Sign-In

For an existing account the server applies, in this order (`backend/open_webui/utils/oauth.py:2027-2092`):

1. **Role**, when **Role Mapping** is on (section 3.2). A refusal stops the sign-in here.
2. **Name**, when **Update Name** is on (code default off): replaced by the **Username Claim** value
   when it differs (`:2038-2047`).
3. **Email**, when **Update Email** is on (code default off): replaced when the claim differs, unless
   another account already uses the new address (then only a log line,
   `Cannot update email to {new_email} for user {user.id} because it is already taken.`). The change
   is made through the account's sign-in record, so accounts without one (SCIM-created accounts)
   keep their old email (`:2049-2062`; `backend/open_webui/models/auths.py:196-210`).
4. **Picture**, when **Update Picture** is on (code default off): fetched again at every sign-in and
   stored when it differs. When the provider offers no usable picture the result is the default
   `/user.png`, which then **replaces a photo the person uploaded** (`:2064-2082`, `:1812-1848`).
5. If anything changed, `user.updated` is published with the changed fields (`:2084-2092`).
6. **Groups**, when **Group Mapping** is on (section 5.6).

A person who edits their name or photo in **Settings → Account** therefore sees it reset at their
next SSO sign-in whenever the matching **Update** switch is on.

### 5.5 Role Mapping at Sign-In, Worked Example

The rules are in section 3.2. With fictional settings **Roles Claim** `roles`, **Allowed Roles**
`staff, user` and **Admin Roles** `admin` (`backend/open_webui/utils/oauth.py:1546-1608`):

| Person (fictional) | `roles` claim received | Result |
|---|---|---|
| jane.doe@example.com, new | `["staff"]` | Account created as `user` (with **OAuth Signup** on) |
| john.roe@example.com, currently `pending` | `["staff"]` | Becomes `user` |
| alex.poe@example.com, currently `admin` | `["staff"]` | **Demoted to `user`** |
| sam.lee@example.com, currently `user` | `["staff", "admin"]` | Becomes `admin` |
| kim.fox@example.com, any | `["student"]` | Refused: `You do not have permission to access this resource. Please contact your administrator for assistance.` |
| lee.ash@example.com, currently `user` | no `roles` claim | Stays `user` (a new person would get `ui.default_user_role`) |

The admin screen fields take comma-separated lists (`backend/open_webui/routers/auths.py:1421-1425`,
`:1475-1477`); the environment variables use `OAUTH_ROLES_SEPARATOR` (code default `,`)
(`backend/open_webui/config.py:2597-2607`).

### 5.6 Group Mapping at Sign-In

Runs at every SSO sign-in, after the session token is issued, and at every token exchange, when
**Group Mapping** (`oauth.enable_group_mapping`, code default off) is on
(`backend/open_webui/utils/oauth.py:2158-2165`; `backend/open_webui/routers/auths.py:1762-1769`).

1. **Read the claim.** **Group Claim** (code default `groups`; the older variable name
   `OAUTH_GROUP_CLAIM` is also accepted) may hold a list, or text split by `OAUTH_GROUPS_SEPARATOR`
   (code default `;`); a dotted name reads a nested value (`backend/open_webui/utils/oauth.py:1654-1671`;
   `backend/open_webui/config.py:2570`, `:2593`).
2. **Create missing groups**, when **Auto-Create Groups** (`oauth.enable_group_creation`, code
   default off) is on. Each claimed name with no MedIT GPT group of that name becomes a new group
   with the description `Group '{group_name}' created automatically via OAuth.`, a copy of the
   current default permissions, and the share setting `OAUTH_GROUP_DEFAULT_SHARE` (code default
   `true`, which the group editor shows as **Anyone**; `members` is also accepted). The group is
   recorded as created by an admin account, or by the person when no admin exists. Blocked names
   are created too, because creation does not consult the blocked list
   (`backend/open_webui/utils/oauth.py:1676-1723`; `backend/open_webui/config.py:2587-2588`).
3. **Remove.** If the claim named at least one group, the person is removed from every group they
   belong to whose name is not in the claim, unless that group matches **Blocked Groups**. This
   includes groups an admin assigned by hand and the **Default Group** (`:1730-1747`).
4. **Add.** The person is added to every existing group whose name is in the claim and does not
   match **Blocked Groups** (`:1765-1784`).
5. **Permission copy.** For every group the person was added to or removed from, if that group has
   no permissions of its own, the current default permissions are written onto the group
   (`:1749-1763`, `:1786-1800`). From then on the group grants whatever the defaults granted at that
   moment, even if an admin later tightens the defaults, because permissions add up across groups
   (ground truth).
6. **Empty or missing claim.** Nothing is removed or added (`:1733`, `:1768`).

Matching is by exact group name, letter case included. **Blocked Groups** entries can be exact
names, shell-style wildcards (`*`, `?`), or regular expressions (any entry containing one of
`^ $ [ ] ( ) { } + \ |`); the field accepts a comma-separated list or a JSON list
(`backend/open_webui/utils/oauth.py:313-364`). Each change publishes `group.member_added` or
`group.member_removed` with source `oauth` (`:1739-1747`, `:1776-1784`).

**Compared with trusted-header groups** (section 5.10):

| Aspect | SSO group mapping | Trusted-header groups header |
|---|---|---|
| When | Every SSO sign-in and token exchange, with **Group Mapping** on | Every trusted-header sign-in, when `WEBUI_AUTH_TRUSTED_GROUPS_HEADER` is set and the header is not empty |
| List format | Claim list, or text split by `;` | Comma-separated header value |
| Creates missing groups | When **Auto-Create Groups** is on | No |
| Respects **Blocked Groups** | Yes | No |
| Removes groups not named | Yes | Yes |
| Copies default permissions onto groups | Yes | No |
| Publishes group events | Yes | No |
| Source | `backend/open_webui/utils/oauth.py:1647-1800` | `backend/open_webui/routers/auths.py:763-768`; `backend/open_webui/models/groups.py:516-572` |

LDAP group mapping is described in `authentication-and-sign-in.md`.

### 5.7 Signing Out of an SSO Session

The basics (which cookies are cleared, revocation needing Redis, other devices staying signed in)
are in `authentication-and-sign-in.md`. What is specific to SSO
(`backend/open_webui/routers/auths.py:955-1059`):

1. The person chooses **Sign Out** in the user menu; the browser calls
   `POST /api/v1/auths/signout` (`src/lib/components/layout/Sidebar/UserMenu.svelte:579-594`).
2. If the browser holds an `oauth_session_id` cookie, the server looks up that stored SSO session,
   records the sign-out as `auth.logout` with source `oauth`, and deletes the `oauth_session_id`
   cookie with the others (`:967-995`).
3. It then picks a provider sign-out address:
   - **`OPENID_END_SESSION_ENDPOINT`** (`oauth.end_session_endpoint`) set: that address, unchanged
     (`:997-1008`).
   - Otherwise, when the stored session was found: the server reads the provider's discovery
     document (the provider's own, or `OPENID_PROVIDER_URL` for a provider without one, such as
     GitHub) and, if it names an end-session endpoint, returns that address with the parameters the
     standard expects, including `post_logout_redirect_uri` set to `WEBUI_AUTH_SIGNOUT_REDIRECT_URL`
     when that variable is set (`:1010-1037`).
   - The discovery document cannot be read: HTTP 500 with
     `Failed to sign out from the OpenID provider.`; from the user menu nothing visible happens
     (`:1038-1047`; `authentication-and-sign-in.md`).
   - No stored session (for example removed by the session limit in section 5.8 or by back-channel
     logout), or no end-session endpoint in the document: no provider sign-out;
     `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` is used if set (`:1049-1059`).
4. The browser forgets the token and goes to the returned address. If that address does not already
   name a return address, the browser adds `post_logout_redirect_uri` pointing at `/auth` and
   `state=logout`, so a provider that honours them sends the person back to `/auth?state=logout`,
   where **Auto Redirect** does not fire (`src/lib/apis/auths/index.ts:382-438`). Whether the U of T
   provider returns people to MedIT GPT, and which return addresses it accepts, is **TO BE
   CONFIRMED**.

At start-up the server logs
`⚠️  OAuth providers configured ({provider_list}) but OPENID_PROVIDER_URL not set - logout will not work!`
when Google, Microsoft, GitHub or Feishu is configured without `OPENID_PROVIDER_URL` or
`OPENID_END_SESSION_ENDPOINT` (`backend/open_webui/config.py:2761-2779`). Step 3 still uses Google's
and Microsoft's own discovery documents, so the warning may overstate the problem for those two
(section 14).

### 5.8 Sessions and Cookies After SSO

The callback sets these cookies (`backend/open_webui/utils/oauth.py:2185-2252`;
`backend/open_webui/main.py:2649-2674`):

| Cookie | Lifetime | Purpose |
|---|---|---|
| `token` | `auth.jwt_expiry` (code default four weeks) | The MedIT GPT session token. The sign-in page reads it once and keeps the token in local storage (`src/routes/auth/+page.svelte:127-152`) |
| `oauth_session_id` | Same | Names the stored SSO session used for provider sign-out and token forwarding |
| `oauth_id_token` | Same | Older front ends only; set while `ENABLE_OAUTH_ID_TOKEN_COOKIE` is `True` (code default) (`backend/open_webui/env.py:871`) |
| `owui-session` | Managed by the session middleware | Holds the one-time state during the round trip (and is cleared at sign-out) |

`SameSite` and `Secure` come from `WEBUI_AUTH_COOKIE_SAME_SITE` and `WEBUI_AUTH_COOKIE_SECURE` for
the first three and from `WEBUI_SESSION_COOKIE_SAME_SITE` and `WEBUI_SESSION_COOKIE_SECURE` for
`owui-session` (code defaults `lax` and off) (`backend/open_webui/env.py:769-778`).

What people notice:

- **The MedIT GPT session is independent of the provider's.** It lasts `auth.jwt_expiry` from the SSO
  sign-in. Signing out of the provider elsewhere does not end it (only back-channel logout with
  Redis does, section 5.9), and staying signed in to the provider does not extend it. When it ends,
  the person sees `Session expired. Please sign in again.` (`authentication-and-sign-in.md`); with
  **Auto Redirect** on, the next visit to `/auth` forwards to the provider again.
- **Clearing a stale session.** When the browser ends an expired session it also clears the `token`
  cookie, as its code comment says, "so /auth doesn't auto-login and redirect-loop"
  (`src/routes/+layout.svelte:931-950`). Any 401 from the server also deletes `token`,
  `oauth_id_token` and `oauth_session_id` (`backend/open_webui/utils/auth.py:494-506`).
- **Up to ten stored SSO sessions per person per provider.** At each SSO sign-in, once a person has
  `OAUTH_MAX_SESSIONS_PER_USER` (code default `10`) stored sessions for that provider, the oldest
  are removed. The browser whose stored session was removed stays signed in to MedIT GPT, but
  provider sign-out and token forwarding stop working there until it signs in by SSO again
  (`backend/open_webui/utils/oauth.py:2224-2235`; `backend/open_webui/env.py:879`).
- **Provider tokens are refreshed when needed.** When a feature needs the person's provider token
  and it is within five minutes of expiry, the server refreshes it if the provider issued a refresh
  token; if that fails the stored session is deleted and the feature gets no token until the next
  SSO sign-in. The MedIT GPT session is unaffected (`backend/open_webui/utils/oauth.py:1356-1419`,
  `:1448-1529`).
- **Which features use the provider token.** Model connections, tool servers and terminals whose
  authentication type is **OAuth**, and functions, receive the signed-in person's provider access
  token (`backend/open_webui/routers/openai.py:194-205`; `backend/open_webui/utils/tools.py:154-157`;
  `backend/open_webui/routers/terminals.py:171-182`; `backend/open_webui/functions.py:245-266`;
  `backend/open_webui/utils/middleware.py:3796-3829`). Someone signed in by password has no stored
  SSO session, so such connections receive no token for them.

### 5.9 Back-Channel Logout

Lets the identity provider end a person's MedIT GPT sessions when they sign out at the provider. Off
unless `ENABLE_OAUTH_BACKCHANNEL_LOGOUT=True`; the endpoint otherwise answers 404
(`backend/open_webui/env.py:897-901`; `backend/open_webui/main.py:2858-2865`). The provider must be
set up to send its logout notices to `/oauth/backchannel-logout` on the MedIT GPT address; whether
the U of T provider is, is **TO BE CONFIRMED**.

1. The provider sends a signed logout notice to `/oauth/backchannel-logout`.
2. The server works out which registered provider issued it and checks that the notice is genuine
   and addressed to MedIT GPT. A notice that fails is answered with HTTP 400 and an
   `error_description` (section 10.1); people see nothing
   (`backend/open_webui/utils/oauth.py:2271-2400`).
3. It finds the account by that provider's subject identifier. A notice that identifies only a
   provider session, without a subject, signs nobody out; the code's debug log says
   "sid-based lookup not yet supported". No matching account: answered 200, nothing done
   (`:2402-2416`).
4. It deletes **all** of the person's stored sessions in `oauth_session`, for every provider,
   including their tool-server connections, so tools that needed connecting must be connected again
   (`:2427-2430`).
5. **With Redis**, it revokes every MedIT GPT session token issued to the person until then, on every
   device, and disconnects their live connections (`:2432-2434`;
   `backend/open_webui/utils/auth.py:349-371`). On their next action the browser shows
   `Session expired. Please sign in again.`, and after a reload also `Invalid token`
   (`authentication-and-sign-in.md`).
6. **Without Redis**, it logs
   `Back-channel logout: Redis not configured, cannot revoke JWT tokens. OAuth sessions will be deleted but existing JWTs will remain valid until expiry.`
   and the person **stays signed in** to MedIT GPT until their token expires (`:2418-2424`).
7. It answers 200 (`:2447`). The log line for each person signed out includes their email address
   (`:2436-2442`).

### 5.10 Trusted-Header Sign-In

The operator sets `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` to the name of a request header that a reverse
proxy in front of MedIT GPT fills with the signed-in person's email; optional headers carry the name,
groups and role (`backend/open_webui/env.py:802-805`). Which proxy, and which identity provider
behind it, production uses (if any) is **TO BE CONFIRMED**.

1. The person opens MedIT GPT. If the proxy has not yet identified them, the proxy shows its own
   sign-in page. When the proxy redirects even the app's first configuration request, the browser
   reloads `/` so that page can appear (`src/lib/apis/index.ts:1469-1516`;
   `src/routes/+layout.svelte:1238-1250`).
2. `/auth` shows `Signing in to {{WEBUI_NAME}}` (displayed as "Signing in to MedIT GPT") with a
   spinner and signs in automatically; no form or buttons are offered
   (`src/routes/auth/+page.svelte:199-200`, `:235-248`; `backend/open_webui/main.py:2331`).
3. The server reads the email header and lower-cases it (`backend/open_webui/routers/auths.py:732-737`).
   - Header missing:
     `Your provider has not provided a trusted header. Please contact your administrator for assistance.`
     appears as a red pop-up and the spinner stays (`:734-735`).
   - This sign-in goes through the same endpoint as password sign-in, so with
     `ENABLE_PASSWORD_AUTH=False` it is refused with
     `The requested action has been restricted as a security measure.` (`:724-728`).
4. **Unknown email:** an account is created at once, **even when New Sign Ups is off**, named from
   the name header (URL-decoded) or else the email, with a random password nobody knows, the default
   role (the very first account becomes `admin` and **New Sign Ups** is switched off) and the default
   group (`:740-759`, `:841-896`).
5. The account must have an active sign-in record with that email. Accounts without one, such as
   SCIM-created accounts, are refused with
   `The email or password provided is incorrect. Please check for typos and try logging in again.`
   (`:761`, `:830-833`; `backend/open_webui/models/auths.py:178-194`).
6. **Groups header** (`WEBUI_AUTH_TRUSTED_GROUPS_HEADER`, comma-separated): memberships are replaced
   to match, as compared in section 5.6 (`backend/open_webui/routers/auths.py:763-768`).
7. **Role header** (`WEBUI_AUTH_TRUSTED_ROLE_HEADER`): `admin`, `user` or `pending` (any letter case)
   sets the role; any other value is ignored with the log line
   `Ignoring invalid trusted role header value: {trusted_role}` (`:770-786`).
8. The session token is issued as for a password sign-in and the page shows `You're now logged in.`
   (`:830-831`; `src/routes/auth/+page.svelte:47-71`).

Afterwards:

- **Every request is checked against the header.** If the proxy now reports a different email from
  the session's account, the server answers `User mismatch. Please sign in again.` (HTTP 401); the
  browser ends the session (`Session expired. Please sign in again.`) and `/auth` signs in as the
  person the proxy now reports (`backend/open_webui/utils/auth.py:462-468`;
  `authentication-and-sign-in.md`).
- **The name header is used only when the account is created**; later name changes at the proxy do
  not reach MedIT GPT (`backend/open_webui/routers/auths.py:747-759`).
- **Sign Out signs straight back in.** `/auth?state=logout` still runs the automatic sign-in, so
  unless `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` sends the browser to the proxy's own sign-out, the person
  is signed in again at once (`src/routes/auth/+page.svelte:199-200`;
  `backend/open_webui/routers/auths.py:1049-1057`).
- **Change Password** is refused in this mode (`authentication-and-sign-in.md`).

### 5.11 SCIM Provisioning

SCIM lets an identity provider manage accounts and groups directly. The code describes its SCIM
support as experimental (`backend/open_webui/routers/scim.py:1-6`). Settings
(`backend/open_webui/env.py:903-916`):

- `ENABLE_SCIM=True` (or the older `SCIM_ENABLED`) mounts the endpoints at `/api/v1/scim/v2`.
- `SCIM_TOKEN` is the bearer token the provider's SCIM client presents. It is a credential: never
  reproduce it.
- `SCIM_AUTH_PROVIDER` names the SSO provider (for example `microsoft` or `oidc`) whose subject
  identifiers the SCIM external IDs correspond to. Without it the server logs a warning at start-up
  (section 10.3).

**What the provider can do** (`backend/open_webui/routers/scim.py:498-1200`):

| Operation | Effect in MedIT GPT |
|---|---|
| List or search users (`GET /Users`, up to 100 per page; filters `userName eq "…"` and `externalId eq "…"`) | Returns only accounts linked to an SSO provider or created by SCIM; password-only, LDAP and trusted-header accounts with no SSO link are invisible to SCIM (`backend/open_webui/models/users.py:488-540`). An `externalId` search falls back to the SSO subject of the `SCIM_AUTH_PROVIDER` provider (`backend/open_webui/routers/scim.py:319-327`) |
| Create a user (`POST /Users`) | Refused with 409 if the external ID or the email already exists. Email: the primary email (else `userName`), lower-cased. Name: `name.formatted`, else given and family names, else `displayName`. Role: `user` if active, else `pending`. **No password record and no default group.** A `password` value is accepted but not used. Publishes `user.created` with source `scim` (`:573-656`) |
| Replace or patch a user (`PUT`, `PATCH /Users/{id}`) | Changes email, name, photo and external ID; `active` maps to `user` or `pending` except for existing admins. The email is changed on the profile only, not on any sign-in record (`:659-839`) |
| Delete a user (`DELETE /Users/{id}`) | Permanent: group memberships, chats and the account are removed, as with deletion from the admin panel; other owned content stays (`:842-872`; `backend/open_webui/models/users.py:849-863`; ground truth). An account's sign-in record, if it had one, is not removed by this path (section 6.4) |
| List, read, create, replace, patch and delete groups (`/Groups`) | Groups are addressed by MedIT GPT group ID (the list can also be filtered with `displayName eq "…"`); members are MedIT GPT user IDs. A new group has a name, an empty description, no permissions and the default share setting, and is recorded as created by an admin account (refused with 500 `No admin user found` if there is none). A `PUT` with `members`, or a `PATCH` that replaces `members`, replaces the whole membership list; a `PATCH` can also add members or remove one (`backend/open_webui/routers/scim.py:876-1200`; `backend/open_webui/models/groups.py:137-145`) |

**How a SCIM-created account signs in.** It has no password record, so email-and-password, LDAP and
trusted-header sign-in all fail with their generic messages. Through SSO, the first sign-in finds no
subject link, so it succeeds only when **Merge Accounts by Email** is on and the provider's email
equals the SCIM email; the account is then linked and later sign-ins match by subject
(`backend/open_webui/utils/oauth.py:2010-2019`). With merge off the person sees
`Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.`
(OAuth Signup on) or the permission message (off).

**Interplay with SSO mapping.** At every SSO sign-in, role mapping and group mapping can override
what SCIM set (sections 3.2 and 5.6). Which source should govern roles and groups is an
organizational decision, **TO BE CONFIRMED**.

**A configuration trap.** When `SCIM_AUTH_PROVIDER` is not set and the provider creates a user
without an external ID, the account is stored first and the request then fails with HTTP 500
`SCIM_AUTH_PROVIDER environment variable is required when SCIM is enabled`; the stored account is
not marked as SCIM-managed, so SCIM cannot see it, and retries fail with
`User with email {email} already exists` (`backend/open_webui/routers/scim.py:306-316`, `:622-642`).
Read from the code, not exercised.

### 5.12 Token Exchange (Programs Only)

Off unless `ENABLE_OAUTH_TOKEN_EXCHANGE=True` (`backend/open_webui/env.py:881-895`). A program sends
an access token it obtained from a registered provider to
`POST /api/v1/auths/oauth/{provider}/token/exchange` and receives a MedIT GPT session token
(`backend/open_webui/routers/auths.py:1624-1771`):

1. The optional `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` (per `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT_WINDOW`
   seconds, code default 180) can refuse with `API rate limit exceeded` (`:94-101`, `:1642-1648`).
2. The provider must be registered; with `OAUTH_TOKEN_EXCHANGE_TRUSTED_CLIENT_IDS` set, the token must
   also have been issued to one of those clients (`:1650-1679`).
3. The provider must confirm the token and return a subject and an email; the email domain must be
   allowed (refused with the permission message here, not the password message) (`:1681-1730`).
4. The account must already exist (found by subject, or by email when merge is on): the exchange never
   creates accounts and answers `User not found. Please sign in via the web interface first.`
   (`:1732-1752`).
5. Role mapping and group mapping apply as at an SSO sign-in (`:1754-1769`).

### 5.13 Connecting a Tool Server (a User's View)

Some MCP tool servers require each person to sign in to the tool's own service. An admin sets this
up (types **OAuth 2.1** and **OAuth 2.1 (Static)**; detail in
`workspace-tools-tool-servers-mcp-and-terminals.md`). For each person, such a tool is listed as not
connected until they connect (`backend/open_webui/routers/tools.py:134-171`).

1. **Prompted.** In a new chat whose model uses such a tool by default, the tool appears as an amber
   chip with the hover text `Click to connect`, and the page may forward the browser to the tool's
   sign-in once by itself. Sending is blocked with
   `Please connect all required integrations before sending a message`
   (`src/lib/components/chat/Chat.svelte:951-968`, `:1038-1055`, `:3130-3133`;
   `src/lib/components/chat/MessageInput.svelte:2546-2559`). Choosing an unconnected tool in the
   integrations menu does the same (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:245-258`).
2. **Connecting.** The draft is saved and the browser goes to `/oauth/clients/mcp:<server id>/authorize`,
   then to the tool's sign-in service, then back to `/oauth/clients/mcp:<server id>/callback`, and
   finally to `/` with the tool selected (`src/lib/components/chat/Chat.svelte:4073-4085`, `:2198-2204`;
   `src/lib/apis/configs/index.ts:568-576`; `backend/open_webui/main.py:2772-2825`).
3. **Failures on the way out** appear as a bare error page: `{"detail":"Not Found"}` when the tool's
   connection details cannot be loaded (including when the stored registration is unreadable, which
   the server log reports with "reconnect this tool server"), `Failed to re-register OAuth client`,
   `OAuth client registration is still invalid after re-registration`, or the message about the
   authorization endpoint in section 10.1 (`backend/open_webui/main.py:2780-2812`;
   `backend/open_webui/utils/oauth.py:885-936`, `:1194-1232`).
4. **Failures on the way back** appear as a red pop-up on the home page, beginning
   `OAuth callback failed:` (`backend/open_webui/utils/oauth.py:1305-1324`;
   `src/routes/(app)/+page.svelte:8-12`).
5. **Staying connected.** The connection's token is refreshed when needed; if refreshing fails, the
   connection is deleted and the tool shows as not connected again
   (`backend/open_webui/utils/oauth.py:1042-1080`). Back-channel logout also deletes it (section 5.9).
6. **Disconnecting.** In the integrations menu, the unlink button beside a connected tool server
   (hover text `Disconnect OAuth`) removes the person's connection and shows
   `OAuth session disconnected` (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:593-618`;
   `backend/open_webui/routers/auths.py:1067-1093`).

### 5.14 Admin: Viewing or Changing the OAuth / OIDC Settings

1. Open **Settings → Admin → Authentication**; the **OAuth / OIDC** section is below LDAP. It loads
   from `GET /api/v1/auths/admin/config/oauth`; if that request fails, the section is simply absent
   (`src/lib/components/admin/Settings/Authentication.svelte:122-124`, `:546`).
2. While `ENABLE_OAUTH_PERSISTENT_CONFIG` is off (code default), a yellow notice reads
   `These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.`
   (shown with `ENABLE_OAUTH_PERSISTENT_CONFIG`), every field is greyed out, and **Save** skips the
   section (`:550-564`, `:77-78`).
3. With it on, changes are saved with the rest of the tab by **Save**, which shows
   `Settings saved successfully!` only when every part saved; a failure shows the server's text
   (`:98-107`, `:77-87`).
4. Only the generic OIDC provider's fields appear; Google, Microsoft, GitHub and Feishu are configured
   only through the environment (`:575-693`). Which fields take effect at once and which need an
   environment change and a restart is in section 7.3.

## 6. Data Model

Live rows are data and are **TO BE CONFIRMED**; nothing below was read from a database.

### 6.1 Columns of the `user` Table Used Here

| Column | Use in this area | Source |
|---|---|---|
| `email` | Matched case-insensitively for merge by email, OAuth sign-up conflicts, trusted headers and SCIM | `backend/open_webui/models/users.py:149`, `:438-452` |
| `name`, `profile_image_url` | Set at SSO, trusted-header or SCIM creation; refreshed at SSO sign-in by **Update Name** and **Update Picture**; changed by SCIM updates | `backend/open_webui/utils/oauth.py:2036-2082`; `backend/open_webui/routers/scim.py:676-699` |
| `role` | Set by role mapping, the trusted role header and SCIM's `active` flag (section 3.2) | `backend/open_webui/models/users.py:151`, `:731-738` |
| `oauth` | JSON `{"<provider>": {"sub": "<subject>"}}`, one entry per linked provider; shown to admins as **OAuth ID** | `backend/open_webui/models/users.py:172`, `:777-792` |
| `scim` | JSON `{"<SCIM_AUTH_PROVIDER>": {"external_id": "<id>"}}`; marks SCIM-managed accounts | `backend/open_webui/models/users.py:173`, `:794-812` |

SCIM sees only accounts whose `oauth` or `scim` value is set (`backend/open_webui/models/users.py:488-540`).

### 6.2 The Sign-In Record (`auth`)

SSO-created and trusted-header-created accounts get an `auth` row like any other account, with a
password nobody knows (`backend/open_webui/utils/oauth.py:2117-2125`;
`backend/open_webui/routers/auths.py:749-756`). SCIM-created accounts get **no** `auth` row, because
SCIM inserts only the `user` row (`backend/open_webui/routers/scim.py:622-629`). That is why they
cannot use password, LDAP or trusted-header sign-in, and why **Update Email** cannot change their
email (`backend/open_webui/models/auths.py:178-210`).

### 6.3 The `oauth_session` Table

One row per stored provider sign-in (`backend/open_webui/models/oauth_sessions.py:23-39`; created by
migration `backend/open_webui/migrations/versions/38d63c18f30f_add_oauth_session_table.py`):

| Column | Meaning |
|---|---|
| `id` | The value of the `oauth_session_id` cookie for SSO sign-ins |
| `user_id` | The MedIT GPT account |
| `provider` | `google`, `microsoft`, `github`, `oidc` or `feishu` for SSO; `mcp:<server id>` for a tool-server connection |
| `token` | The provider's tokens for that sign-in. These are credentials: never export or share them |
| `expires_at`, `created_at`, `updated_at` | Epoch seconds; `expires_at` is the provider access token's expiry |

Rows are added at each SSO sign-in (one per browser) and each tool-server connection (one per person
per tool server; a new connection replaces the old). Rows are removed by the per-person limit
(section 5.8), a failed refresh, **Disconnect OAuth**, and back-channel logout
(`backend/open_webui/utils/oauth.py:1074`, `:1286-1290`, `:1412`, `:2233-2235`, `:2428-2430`;
`backend/open_webui/routers/auths.py:1079`). Their wider lifecycle is listed as security-sensitive
in section 14.

### 6.4 What Deletion Leaves Behind

- **SCIM deletion** removes group memberships, chats and the `user` row through the same routine the
  admin panel uses, but unlike the admin panel it does not remove the account's `auth` row, so a
  sign-in record holding the email address can remain for accounts that had one
  (`backend/open_webui/routers/scim.py:857`; `backend/open_webui/models/users.py:849-863`; compare
  `backend/open_webui/models/auths.py:228-239`). Personal data: escalate clean-up questions to the
  platform maintainer.
- Content other than chats stays behind after any deletion (ground truth).

### 6.5 Settings Rows and Other Stores

| Store | What this area keeps there | Source |
|---|---|---|
| `config` rows `oauth.*` | Only when `ENABLE_OAUTH_PERSISTENT_CONFIG=True`; otherwise these values live in each server process's memory, rebuilt from the environment at start-up | `backend/open_webui/models/config.py:133-147`, `:198-206`, `:254-257` |
| `config` rows used here | `webui.url` (where SSO returns people), `ui.default_user_role`, `ui.default_group_id`, `auth.jwt_expiry`, `user.permissions` (copied onto groups by group mapping), `tool_server.connections` (tool-server OAuth registration) | `backend/open_webui/utils/oauth.py:131-184`, `:2137`, `:2163`, `:2175`; `backend/open_webui/main.py:2683` |
| `group` rows created by SSO | Description `Group '{group_name}' created automatically via OAuth.`, permissions copied from the defaults, share setting from `OAUTH_GROUP_DEFAULT_SHARE` | `backend/open_webui/utils/oauth.py:1690-1695` |
| Browser local storage | `token` (the session token), `redirectPath` (page to return to) | `src/routes/auth/+page.svelte:52`, `:69`, `:150-151`, `:163-165` |
| Browser session storage | `pendingOAuthToolId`, `oauthRedirectInProgressToolId` during a tool-server connection | `src/lib/apis/configs/index.ts:568-576` |
| Browser cookies | `token`, `oauth_session_id`, `oauth_id_token`, `owui-session` (section 5.8) | `backend/open_webui/utils/oauth.py:2185-2252` |
| Redis (optional) | The per-person revocation marker set by back-channel logout; `owui-session` contents when `ENABLE_STAR_SESSIONS_MIDDLEWARE=True` | `backend/open_webui/utils/auth.py:349-371`; `backend/open_webui/main.py:2649-2664` |

### 6.6 Personal Data in This Area

- **Server logs** record the provider's full claims (names, emails, groups) when an SSO sign-in fails
  for a missing subject, missing email or disallowed domain, and the email of everyone signed out by
  back-channel logout (`backend/open_webui/utils/oauth.py:1952`, `:1998`, `:2007`, `:2436-2442`).
- **Event webhooks** and event functions receive `user.created`, `user.updated`, `user.role_updated`,
  `user.deleted` (whose data includes the email, for SCIM), `auth.login`, `auth.logout` and group
  membership events with source `oauth`, `trusted_header` or `scim`
  (`backend/open_webui/events.py:1034-1057`, `:1171`; `backend/open_webui/routers/scim.py:864-870`).
  Which webhooks production has is in `admin-settings-panels.md` and is **TO BE CONFIRMED**.
- **SCIM responses** return names, emails, photos and group memberships to the identity provider
  (`backend/open_webui/routers/scim.py:330-369`).
- **Trusted-header sign-in** writes the email address to the server log at every sign-in, in the
  log line `authenticate_user_by_email: {email}` (`backend/open_webui/models/auths.py:184`).
- **Update Email conflicts** are logged with the new address
  (`backend/open_webui/utils/oauth.py:2056-2058`). Like SCIM `user.deleted`, SCIM `user.created`
  events carry the account's email, plus its external ID (`backend/open_webui/routers/scim.py:644-654`).
- **Admin views.** The admin user editor shows each linked provider's subject identifier
  (**OAuth ID**), a permanent identifier for the person at the identity provider
  (`src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198`).
- **Stored SSO and tool-server sessions** (section 6.3) hold the person's provider tokens. They are
  credentials as well as personal data: never export, copy or share them.

## 7. Settings and Configuration

Defaults below are what the code says. **Every live value is data held in the server environment
(or, for stored keys, the `config` table) and is TO BE CONFIRMED for production.** Labels and
descriptions are the English text from `src/lib/i18n/locales/en-US/translation.json`; admins can
override wording (`ui.i18n`, described in `authentication-and-sign-in.md`).

### 7.1 Where Single Sign-On Settings Come From

The `oauth.*` keys behave differently from every other persistent setting (ground truth):

| Switch (environment variable) | Code default | Effect on the `oauth.*` keys | Source |
|---|---|---|---|
| `ENABLE_OAUTH_PERSISTENT_CONFIG` | `False` | **Off:** every `oauth.*` value is rebuilt from the environment at each start and held only in each server process's memory; nothing is written to the `config` table, and the admin **OAuth / OIDC** section is read-only. **On:** a key without a stored row is seeded from the environment at start-up, and from then on the stored value wins over the environment, as for other persistent settings | `backend/open_webui/config.py:3232-3238`; `backend/open_webui/models/config.py:133-147`, `:241-266`; `src/lib/components/admin/Settings/Authentication.svelte:52`, `:550-564` |
| `ENABLE_PERSISTENT_CONFIG` | `True` | `False` makes every key, `oauth.*` included, environment-only | `backend/open_webui/config.py:3231`; `backend/open_webui/models/config.py:134-135` |
| `RESET_CONFIG_ON_START` | `False` | `True` deletes every stored setting at each start, before the environment defaults are seeded again | `backend/open_webui/env.py:368`; `backend/open_webui/main.py:363-367`; `backend/open_webui/config.py:42-49` |

What follows from this:

- **Admin edits while persistence is off are per process and temporary.** The admin screen greys
  the section out and its **Save** skips it, but the save endpoint itself does not check the
  switch. A request that reaches it changes the value only in the memory of the one server process
  that handled it, and the change is lost at the next restart
  (`backend/open_webui/routers/auths.py:1511-1514`; `backend/open_webui/models/config.py:198-206`).
  Other server processes keep the environment value. How many processes production runs is
  **TO BE CONFIRMED**.
- **Switching persistence on later** makes any `oauth.*` rows already stored in the `config` table
  win at once; keys without a row are seeded from the environment at that start
  (`backend/open_webui/models/config.py:141-147`, `:241-266`).
- **With persistence on, environment changes stop affecting stored keys**, but provider
  registration still follows the environment (section 7.3).
- The admin section learns the switch's state from `ENABLE_OAUTH_PERSISTENT_CONFIG` in the settings
  it loads (`backend/open_webui/routers/auths.py:1483-1491`).

### 7.2 Authentication Tab: OAuth / OIDC

The section titled `OAuth / OIDC` (`src/lib/i18n/locales/en-US/translation.json:2119`) sits below
LDAP. Everything after the first switch appears only while **OAuth / OIDC** is on; the role fields
only while **Role Mapping** is on; the group fields only while **Group Mapping** is on
(`src/lib/components/admin/Settings/Authentication.svelte:573`, `:749`, `:802`). Only the generic
OIDC provider has fields here; Google, Microsoft, GitHub and Feishu are configured only in the
environment (section 7.4).

| Label | Description (verbatim) | Key | Environment variable and code default | Field hint and notes | Source |
|---|---|---|---|---|---|
| OAuth / OIDC | `Allow users to authenticate with an OAuth / OIDC provider.` | `oauth.enable` | `ENABLE_OAUTH`, `True` | Switch. Off hides every SSO button and makes `/oauth/{provider}/login` answer 404, without clearing provider settings | `src/lib/components/admin/Settings/Authentication.svelte:565-571`; `src/lib/i18n/locales/en-US/translation.json:2090-2091`; `backend/open_webui/config.py:2478-2481`; `backend/open_webui/main.py:2317-2326` |
| Provider Name | `Display name shown for the OAuth provider.` | `oauth.provider_name` | `OAUTH_PROVIDER_NAME`, `SSO` | Placeholder `SSO`. The button label comes from the environment value at start-up; editing this field does not change it (section 7.3) | `src/lib/components/admin/Settings/Authentication.svelte:575-584`; `src/lib/i18n/locales/en-US/translation.json:2102-2103`; `backend/open_webui/config.py:2559`, `:2732-2735`; `backend/open_webui/main.py:2321` |
| Provider URL | `OpenID discovery URL for this provider.` | `oauth.provider_url` | `OPENID_PROVIDER_URL`, empty | Placeholder is an upstream example (a Google address). Required to register `oidc`; also the discovery address used at sign-out for providers without their own | `src/lib/components/admin/Settings/Authentication.svelte:586-595`; `src/lib/i18n/locales/en-US/translation.json:2104-2105`; `backend/open_webui/config.py:2545`, `:2712`; `backend/open_webui/routers/auths.py:1010-1013` |
| Client ID | `OAuth client identifier from the provider.` | `oauth.client_id` | `OAUTH_CLIENT_ID`, empty | Placeholder `Enter Client ID` | `src/lib/components/admin/Settings/Authentication.svelte:599-608`; `src/lib/i18n/locales/en-US/translation.json:2054-2055`; `backend/open_webui/config.py:2541` |
| Client Secret | `OAuth client secret from the provider.` | `oauth.client_secret` | `OAUTH_CLIENT_SECRET`, empty | Placeholder `Enter Client Secret`. A credential: never copy its value into a ticket | `src/lib/components/admin/Settings/Authentication.svelte:610-620`; `src/lib/i18n/locales/en-US/translation.json:2056-2057`; `backend/open_webui/config.py:2543` |
| Redirect URI | `Callback URI registered with the provider.` | `oauth.redirect_uri` | `OPENID_REDIRECT_URI`, empty | Placeholder `Enter Redirect URI`. When empty the server builds `/oauth/oidc/login/callback` on the address the request arrived on | `src/lib/components/admin/Settings/Authentication.svelte:624-633`; `src/lib/i18n/locales/en-US/translation.json:2106-2107`; `backend/open_webui/config.py:2549`; `backend/open_webui/utils/oauth.py:1860-1862` |
| Scopes | `OAuth scopes requested during sign-in.` | `oauth.scopes` | `OAUTH_SCOPES`, `openid email profile` | Placeholder `openid email profile` | `src/lib/components/admin/Settings/Authentication.svelte:635-644`; `src/lib/i18n/locales/en-US/translation.json:2112-2113`; `backend/open_webui/config.py:2551` |
| Email Claim | `Claim used as the user email address.` | `oauth.email_claim` | `OAUTH_EMAIL_CLAIM`, `email` | Placeholder `email` | `src/lib/components/admin/Settings/Authentication.svelte:648-657`; `src/lib/i18n/locales/en-US/translation.json:2062-2063`; `backend/open_webui/config.py:2568` |
| Username Claim | `Claim used as the display name.` | `oauth.username_claim` | `OAUTH_USERNAME_CLAIM`, `name` | Placeholder `name` | `src/lib/components/admin/Settings/Authentication.svelte:659-668`; `src/lib/i18n/locales/en-US/translation.json:2133-2134`; `backend/open_webui/config.py:2563` |
| Picture Claim | `Claim used as the profile picture URL.` | `oauth.picture_claim` | `OAUTH_PICTURE_CLAIM`, `picture` | Placeholder `picture` | `src/lib/components/admin/Settings/Authentication.svelte:672-681`; `src/lib/i18n/locales/en-US/translation.json:2098-2099`; `backend/open_webui/config.py:2566` |
| Sub Claim | `Claim used as the stable user identifier.` | `oauth.sub_claim` | `OAUTH_SUB_CLAIM`, none (each provider's usual claim) | Placeholder `sub`. Changing it breaks existing account links (section 5.3) | `src/lib/components/admin/Settings/Authentication.svelte:683-692`; `src/lib/i18n/locales/en-US/translation.json:2122-2123`; `backend/open_webui/config.py:2561` |
| OAuth Signup | `Allow users to create accounts through OAuth.` | `oauth.enable_signup` | `ENABLE_OAUTH_SIGNUP`, `False` | Switch | `src/lib/components/admin/Settings/Authentication.svelte:695-701`; `src/lib/i18n/locales/en-US/translation.json:2092-2093`; `backend/open_webui/config.py:2483` |
| Merge Accounts by Email | `Link OAuth sign-ins to existing accounts with the same email.` | `oauth.merge_accounts_by_email` | `OAUTH_MERGE_ACCOUNTS_BY_EMAIL`, `False` | Switch. Security note in section 5.3 | `src/lib/components/admin/Settings/Authentication.svelte:703-714`; `src/lib/i18n/locales/en-US/translation.json:2086-2087`; `backend/open_webui/config.py:2490` |
| Auto Redirect | `Send users directly to the OAuth provider from the sign-in page.` | `oauth.auto_redirect` | `OAUTH_AUTO_REDIRECT`, `False` | Switch. Fires only under the conditions in section 5.1 | `src/lib/components/admin/Settings/Authentication.svelte:716-722`; `src/lib/i18n/locales/en-US/translation.json:2046-2047`; `backend/open_webui/config.py:2485` |
| Allowed Domains | `Email domains allowed to sign in with OAuth.` | `oauth.allowed_domains` | `OAUTH_ALLOWED_DOMAINS`, `*` | Placeholder `* (all domains)`. Comma-separated; exact, letter-case-sensitive match (section 5.2, step 8) | `src/lib/components/admin/Settings/Authentication.svelte:724-733`; `src/lib/i18n/locales/en-US/translation.json:2028-2029`; `backend/open_webui/config.py:2609`; `backend/open_webui/routers/auths.py:1475-1477` |
| Role Mapping | `Map OAuth claims to Open WebUI roles.` | `oauth.enable_role_mapping` | `ENABLE_OAUTH_ROLE_MANAGEMENT`, `False` | Switch. Rules in section 3.2 | `src/lib/components/admin/Settings/Authentication.svelte:738-747`; `src/lib/i18n/locales/en-US/translation.json:2108-2109`; `backend/open_webui/config.py:2580` |
| Roles Claim | `Claim containing provider roles.` | `oauth.roles_claim` | `OAUTH_ROLES_CLAIM`, `roles` | Placeholder `roles` | `src/lib/components/admin/Settings/Authentication.svelte:751-760`; `src/lib/i18n/locales/en-US/translation.json:2110-2111`; `backend/open_webui/config.py:2595` |
| Admin Roles | `Provider roles that grant admin access.` | `oauth.admin_roles` | `OAUTH_ADMIN_ROLES`, `admin` | Placeholder `admin`. Comma-separated | `src/lib/components/admin/Settings/Authentication.svelte:762-771`; `src/lib/i18n/locales/en-US/translation.json:2026-2027`; `backend/open_webui/config.py:2605-2607` |
| Allowed Roles | `Provider roles allowed to sign in.` | `oauth.allowed_roles` | `OAUTH_ALLOWED_ROLES`, `user` and `admin` | Placeholder `*`, but an emptied field is saved as "no allowed roles": then only **Admin Roles** values (or an empty roles claim) let people in. Allowing any role needs `*` typed in | `src/lib/components/admin/Settings/Authentication.svelte:774-783`; `src/lib/i18n/locales/en-US/translation.json:2032-2033`; `backend/open_webui/config.py:2599-2603`; `backend/open_webui/routers/auths.py:1475-1477`; `backend/open_webui/utils/oauth.py:1586-1608` |
| Group Mapping | `Map OAuth claims to Open WebUI groups.` | `oauth.enable_group_mapping` | `ENABLE_OAUTH_GROUP_MANAGEMENT`, `False` | Switch. Replaces memberships at each sign-in (section 5.6) | `src/lib/components/admin/Settings/Authentication.svelte:789-800`; `src/lib/i18n/locales/en-US/translation.json:2070-2071`; `backend/open_webui/config.py:2582` |
| Auto-Create Groups | `Create missing groups from OAuth claims.` | `oauth.enable_group_creation` | `ENABLE_OAUTH_GROUP_CREATION`, `False` | Switch | `src/lib/components/admin/Settings/Authentication.svelte:803-814`; `src/lib/i18n/locales/en-US/translation.json:2068-2069`; `backend/open_webui/config.py:2584` |
| Group Claim | `Claim containing provider groups.` | `oauth.group_claim` | `OAUTH_GROUPS_CLAIM` (older `OAUTH_GROUP_CLAIM`), `groups` | Placeholder `groups` | `src/lib/components/admin/Settings/Authentication.svelte:817-826`; `src/lib/i18n/locales/en-US/translation.json:2074-2075`; `backend/open_webui/config.py:2570` |
| Blocked Groups | `Provider groups blocked from signing in.` | `oauth.blocked_groups` | `OAUTH_BLOCKED_GROUPS`, `[]` | Placeholder `Comma-separated group names`. Despite the description, the list only shields memberships from group mapping and blocks nobody (section 4) | `src/lib/components/admin/Settings/Authentication.svelte:828-837`; `src/lib/i18n/locales/en-US/translation.json:2048-2049`; `backend/open_webui/config.py:2591` |
| Update Email | `Refresh the account email from OAuth on sign-in.` | `oauth.update_email_on_login` | `OAUTH_UPDATE_EMAIL_ON_LOGIN`, `False` | Switch (section 5.4) | `src/lib/components/admin/Settings/Authentication.svelte:841-850`; `src/lib/i18n/locales/en-US/translation.json:2127-2128`; `backend/open_webui/config.py:2615` |
| Update Name | `Refresh the account name from OAuth on sign-in.` | `oauth.update_name_on_login` | `OAUTH_UPDATE_NAME_ON_LOGIN`, `False` | Switch (section 5.4) | `src/lib/components/admin/Settings/Authentication.svelte:852-861`; `src/lib/i18n/locales/en-US/translation.json:2129-2130`; `backend/open_webui/config.py:2613` |
| Update Picture | `Refresh the profile picture from OAuth on sign-in.` | `oauth.update_picture_on_login` | `OAUTH_UPDATE_PICTURE_ON_LOGIN`, `False` | Switch (section 5.4) | `src/lib/components/admin/Settings/Authentication.svelte:863-872`; `src/lib/i18n/locales/en-US/translation.json:2131-2132`; `backend/open_webui/config.py:2611` |

The save endpoint also accepts keys that have no field on this screen (`OAUTH_GROUP_DEFAULT_SHARE`,
`OAUTH_CODE_CHALLENGE_METHOD`, `OAUTH_TOKEN_ENDPOINT_AUTH_METHOD`, `OPENID_END_SESSION_ENDPOINT`,
`OAUTH_TIMEOUT`, `OAUTH_CLIENT_TIMEOUT`, `OAUTH_AUDIENCE`, `OAUTH_REFRESH_TOKEN_INCLUDE_SCOPE`); the
screen sends back whatever values it loaded for them (`backend/open_webui/routers/auths.py:1369-1462`;
`src/lib/components/admin/Settings/Authentication.svelte:77-87`).

### 7.3 What Takes Effect at Once and What Needs a Restart

The running server reads some `oauth.*` keys every time it needs them. Others are only displayed,
because each provider was registered once, at start-up, from the environment variables
(`backend/open_webui/config.py:2653-2782`; `backend/open_webui/main.py:524`;
`backend/open_webui/utils/oauth.py:1330-1343`).

| Settings | Read at each use? | An admin edit (persistence on) | An environment change | Source |
|---|---|---|---|---|
| **OAuth / OIDC**, **OAuth Signup**, **Merge Accounts by Email**, **Allowed Domains**, the four claim fields, **Role Mapping** and its fields, **Group Mapping** and its fields, **Blocked Groups**, the three **Update** switches, and `oauth.audience`, `oauth.group_default_share`, `oauth.refresh_token.include_scope` | Yes | Applies from the next sign-in (or token exchange) | Applies after a restart while persistence is off; ignored once a stored row exists while it is on | `backend/open_webui/utils/oauth.py:131-205`; `backend/open_webui/routers/auths.py:1699-1762` |
| **Auto Redirect**, and **OAuth / OIDC** for the list of buttons | Yes, by `/api/config` | Applies when the sign-in page next loads | As above | `backend/open_webui/main.py:2256-2326` |
| `oauth.end_session_endpoint`, and **Provider URL** as the sign-out discovery address | Yes, at **Sign Out** | Applies at the next sign-out | As above | `backend/open_webui/routers/auths.py:997-1013` |
| **Provider Name**, **Client ID**, **Client Secret**, **Redirect URI**, **Scopes**, **Provider URL** for sign-in, `oauth.code_challenge_method`, `oauth.token_endpoint_auth_method`, `oauth.timeout`, `oauth.client.timeout`, and every `oauth.google.*`, `oauth.microsoft.*`, `oauth.github.*` and `oauth.feishu.*` key | No: sign-in uses the registration made at start-up | None on sign-in: the stored value is kept (and, for the screen's fields, displayed) but not used | Applies after a restart, whether or not persistence is on | `backend/open_webui/config.py:2636-2782`; `backend/open_webui/utils/oauth.py:842`, `:1337-1348`; `backend/open_webui/main.py:2317-2324` |

So, with persistence on, an admin who changes the client secret on this screen sees it saved, but
sign-in keeps using the secret from the environment until the environment changes and the server
restarts; the button label likewise follows `OAUTH_PROVIDER_NAME`. Saving writes immediately
(`Config.upsert`); nothing is queued (`backend/open_webui/routers/auths.py:1513`).

### 7.4 Provider Registration (Environment Only)

A provider is registered, and its button shown, only when all the variables in the second column
are set; an incomplete set produces no button and no specific log line
(`backend/open_webui/config.py:2653-2782`).

| Provider | Registered when these are set | Other variables (code default) | Source |
|---|---|---|---|
| `google` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `GOOGLE_OAUTH_SCOPE` (`openid email profile`); `GOOGLE_REDIRECT_URI` (empty); `GOOGLE_OAUTH_AUTHORIZE_PARAMS` (a JSON object of extra sign-in parameters; anything else is ignored with a log line) | `backend/open_webui/config.py:2494-2513`, `:2655-2671` |
| `microsoft` | `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_CLIENT_TENANT_ID` | `MICROSOFT_CLIENT_LOGIN_BASE_URL` (`https://login.microsoftonline.com`); `MICROSOFT_CLIENT_PICTURE_URL` (the Microsoft Graph photo address); `MICROSOFT_OAUTH_SCOPE` (`openid email profile`); `MICROSOFT_REDIRECT_URI` (empty) | `backend/open_webui/config.py:2515-2531`, `:2673-2689` |
| `github` | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | `GITHUB_CLIENT_SCOPE` (`user:email`); `GITHUB_CLIENT_REDIRECT_URI` (empty). Subject claim `id` | `backend/open_webui/config.py:2533-2539`, `:2691-2710` |
| `oidc` | `OAUTH_CLIENT_ID`, `OPENID_PROVIDER_URL`, and either `OAUTH_CLIENT_SECRET` or `OAUTH_CODE_CHALLENGE_METHOD` | `OAUTH_SCOPES` (`openid email profile`); `OPENID_REDIRECT_URI` (empty); `OAUTH_TOKEN_ENDPOINT_AUTH_METHOD` (none); `OAUTH_PROVIDER_NAME` (`SSO`, the button label) | `backend/open_webui/config.py:2541-2559`, `:2712-2735` |
| `feishu` | `FEISHU_CLIENT_ID`, `FEISHU_CLIENT_SECRET` | `FEISHU_OAUTH_SCOPE` (`contact:user.base:readonly`); `FEISHU_REDIRECT_URI` (empty). Subject claim `user_id`; does not use `OAUTH_CODE_CHALLENGE_METHOD` | `backend/open_webui/config.py:2572-2578`, `:2737-2759` |

Common to the registrations: `OAUTH_TIMEOUT` (seconds; empty leaves the library default) and
`OAUTH_CODE_CHALLENGE_METHOD` (`S256` or unset; any other value stops the server at start-up while
Google, Microsoft, GitHub or OIDC is configured) (`backend/open_webui/config.py:2553`, `:2557`,
`:2636-2650`). The production provider and its variables are **TO BE CONFIRMED**.

### 7.5 Other Single Sign-On Settings Not on the Admin Screen

| Variable | Stored key | Code default | Effect | Source |
|---|---|---|---|---|
| `OAUTH_AUDIENCE` | `oauth.audience` | empty | Adds an `audience` parameter to the sign-in request | `backend/open_webui/config.py:2621`; `backend/open_webui/utils/oauth.py:1865-1866` |
| `OAUTH_AUTHORIZE_PARAMS` | none | empty | A JSON object of extra sign-in parameters for every provider; anything else is ignored with a log line | `backend/open_webui/config.py:2623-2633`; `backend/open_webui/utils/oauth.py:1867-1868` |
| `OAUTH_ROLES_SEPARATOR` | none | `,` | Splits a text roles claim and the two role variables | `backend/open_webui/config.py:2597-2607`; `backend/open_webui/utils/oauth.py:1567-1572` |
| `OAUTH_GROUPS_SEPARATOR` | none | `;` | Splits a text groups claim | `backend/open_webui/config.py:2593`; `backend/open_webui/utils/oauth.py:1664-1669` |
| `OAUTH_GROUP_DEFAULT_SHARE` | `oauth.group_default_share` | `true` | Share setting of groups created by group mapping: `true`, `members`, or off for any other value | `backend/open_webui/config.py:2587-2588`; `backend/open_webui/utils/oauth.py:1694` |
| `OAUTH_REFRESH_TOKEN_INCLUDE_SCOPE` | `oauth.refresh_token.include_scope` | `False` | Sends the scopes again when refreshing a provider token | `backend/open_webui/config.py:2487`; `backend/open_webui/utils/oauth.py:1495-1501`, `:1158-1164` |
| `OAUTH_ACCESS_TOKEN_REQUEST_INCLUDE_CLIENT_ID` | none | `False` | Adds the client ID to the code exchange at the callback | `backend/open_webui/config.py:2617-2619`; `backend/open_webui/utils/oauth.py:1886-1887` |
| `ENABLE_OAUTH_EMAIL_FALLBACK` | none | `False` | Gives a person without an email claim a made-up address `{provider}@{sub}.local` instead of refusing | `backend/open_webui/env.py:869`; `backend/open_webui/utils/oauth.py:1995-1996` |
| `OPENID_END_SESSION_ENDPOINT` | `oauth.end_session_endpoint` | empty | A fixed provider sign-out address (section 5.7) | `backend/open_webui/config.py:2547`; `backend/open_webui/routers/auths.py:997-1008` |
| `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` | none | none | Where the browser goes after signing out; also passed to the provider as the return address | `backend/open_webui/env.py:864`; `backend/open_webui/routers/auths.py:1027-1034`, `:1049-1057` |
| `ENABLE_OAUTH_ID_TOKEN_COOKIE` | none | `True` | Sets the older `oauth_id_token` cookie | `backend/open_webui/env.py:871`; `backend/open_webui/utils/oauth.py:2211-2219` |
| `OAUTH_MAX_SESSIONS_PER_USER` | none | `10` | Stored SSO sessions kept per person per provider (section 5.8) | `backend/open_webui/env.py:879`; `backend/open_webui/utils/oauth.py:2224-2235` |
| `WEBUI_AUTH_COOKIE_SAME_SITE`, `WEBUI_AUTH_COOKIE_SECURE`, `WEBUI_SESSION_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE` | none | `lax`, off | Cookie flags (section 5.8) | `backend/open_webui/env.py:769-778` |
| `ENABLE_STAR_SESSIONS_MIDDLEWARE` | none | `False` | Keeps the `owui-session` data in Redis | `backend/open_webui/env.py:967`; `backend/open_webui/main.py:2649-2674` |
| `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY`, `OAUTH_CLIENT_INFO_ENCRYPTION_KEY` | none | the server's secret key | Secrets that protect stored SSO sessions and tool-server registrations: never reproduce; location only. After a change (or a change of the secret key they default to) existing stored sessions and registrations can no longer be read, so people reconnect tool servers and sign in by SSO again (section 11) | `backend/open_webui/env.py:873-875` |

### 7.6 Trusted Headers (Environment Only)

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` | none | The header carrying the email. When set, the sign-in page signs in automatically and every request is checked against the header | `backend/open_webui/env.py:802`; `backend/open_webui/routers/auths.py:732-737`; `backend/open_webui/utils/auth.py:462-468`; `backend/open_webui/main.py:2331` |
| `WEBUI_AUTH_TRUSTED_NAME_HEADER` | none | The display name, used only when the account is created | `backend/open_webui/env.py:803`; `backend/open_webui/routers/auths.py:740-759` |
| `WEBUI_AUTH_TRUSTED_GROUPS_HEADER` | none | Comma-separated group names; memberships are replaced at each sign-in | `backend/open_webui/env.py:804`; `backend/open_webui/routers/auths.py:763-768` |
| `WEBUI_AUTH_TRUSTED_ROLE_HEADER` | none | `admin`, `user` or `pending` sets the role at each sign-in | `backend/open_webui/env.py:805`; `backend/open_webui/routers/auths.py:770-786` |
| `ENABLE_PASSWORD_AUTH` | `True` | `False` also refuses trusted-header sign-in | `backend/open_webui/config.py:1670`; `backend/open_webui/routers/auths.py:724-728` |

Trusted-header mode relies on the proxy being the only way to reach MedIT GPT. How production
ensures that is **Security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca)**.

### 7.7 SCIM (Environment Only)

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `ENABLE_SCIM` (older `SCIM_ENABLED`) | `False` | Mounts `/api/v1/scim/v2` at start-up | `backend/open_webui/env.py:907`; `backend/open_webui/main.py:885-887` |
| `SCIM_TOKEN` | empty | The bearer token the identity provider's SCIM client presents. A secret: never reproduce. While it is empty every SCIM request is refused | `backend/open_webui/env.py:908`; `backend/open_webui/routers/scim.py:269-276` |
| `SCIM_AUTH_PROVIDER` | empty | The SSO provider (for example `microsoft` or `oidc`) whose subject identifiers the SCIM external IDs match; a start-up warning appears when SCIM is on without it | `backend/open_webui/env.py:909-916`; `backend/open_webui/routers/scim.py:306-327` |

### 7.8 Back-Channel Logout and Token Exchange (Environment Only)

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` | `False` | Enables `POST /oauth/backchannel-logout` (otherwise 404) | `backend/open_webui/env.py:897-901`; `backend/open_webui/main.py:2858-2865` |
| `REDIS_URL` (or the Sentinel and Cluster settings) | none | Without Redis, back-channel logout deletes stored sessions but cannot end MedIT GPT sessions (section 5.9) | `backend/open_webui/env.py:381`; `backend/open_webui/utils/oauth.py:2418-2434` |
| `ENABLE_OAUTH_TOKEN_EXCHANGE` | `False` | Enables the token-exchange endpoint (otherwise 403) | `backend/open_webui/env.py:883`; `backend/open_webui/routers/auths.py:1636-1640` |
| `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` | none (no limit) | Optional limit on token-exchange requests per window; `none` or empty means no limit | `backend/open_webui/env.py:884-889`; `backend/open_webui/routers/auths.py:92-99`, `:1642-1648` |
| `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT_WINDOW` | `180` seconds | The window for that limit | `backend/open_webui/env.py:890` |
| `OAUTH_TOKEN_EXCHANGE_TRUSTED_CLIENT_IDS` | empty | When set, only tokens issued to these client IDs are exchanged; the provider must then offer token introspection | `backend/open_webui/env.py:891-895`; `backend/open_webui/routers/auths.py:1594-1622`, `:1668-1679` |

### 7.9 Tool-Server OAuth Settings That Touch This Area

Configured by admins in the tool-server settings; depth is in
`workspace-tools-tool-servers-mcp-and-terminals.md`.

| Setting | Code default | Effect here | Source |
|---|---|---|---|
| `OAUTH_CLIENT_TIMEOUT` (`oauth.client.timeout`) | empty | Timeout in seconds for requests to tool servers' sign-in services; read at start-up | `backend/open_webui/config.py:390`, `:2834`; `backend/open_webui/utils/oauth.py:842` |
| `tool_server.connections` | from `TOOL_SERVER_CONNECTIONS` | Each tool server's connection, including its OAuth registration; loaded at start-up and rewritten when a registration is repaired | `backend/open_webui/main.py:621-656`, `:2747-2758`; `backend/open_webui/routers/configs.py:172-209` |

### 7.10 Related Settings Outside `oauth.*`

These are ordinary persistent settings: after the first start the stored value wins (ground truth).

| Setting | Code default | Effect here | Source |
|---|---|---|---|
| `webui.url` (`WEBUI_URL`) | empty | Where SSO returns people (`/auth` on this address) and the base of tool-server callback addresses; when empty, the address the request arrived on | `backend/open_webui/config.py:1661`, `:3082`; `backend/open_webui/utils/oauth.py:514-522`, `:1318-1319`, `:2175-2177` |
| `ui.default_user_role` (`DEFAULT_USER_ROLE`) | `pending` | Role of new SSO and trusted-header accounts when role mapping is off or the claim is empty | `backend/open_webui/config.py:1720`, `:3096`; `backend/open_webui/utils/oauth.py:132`, `:1609-1612`; `backend/open_webui/routers/auths.py:868` |
| `ui.default_group_id` (`DEFAULT_GROUP_ID`) | empty | Group given to new SSO and trusted-header accounts; SCIM-created accounts do not get it | `backend/open_webui/config.py:1722`, `:3097`; `backend/open_webui/utils/oauth.py:2137-2138`; `backend/open_webui/routers/auths.py:881-885` |
| `auth.jwt_expiry` (`JWT_EXPIRES_IN`) | `4w` | Lifetime of the MedIT GPT session after SSO and of the SSO cookies | `backend/open_webui/config.py:2466`, `:3158`; `backend/open_webui/utils/oauth.py:2154-2157`, `:2185-2187` |
| `user.permissions` | the default permission set | Copied onto groups by group mapping (section 5.6) | `backend/open_webui/utils/oauth.py:2163`; `backend/open_webui/routers/auths.py:1767` |

## 8. Cron Jobs and Background Processes

There is no crontab and no scheduled job in this area. None of the seven background loops the
server starts (`knowledgebase/tools/inventory.md`: `automation_worker_loop`,
`periodic_session_pool_cleanup`, `periodic_usage_pool_cleanup`, `redis_event_listener`,
`redis_task_command_listener`, `redis_task_heartbeat`, `scheduler_worker_loop`) handles sign-in,
stored SSO or tool-server sessions, or SCIM (`backend/open_webui/socket/main.py:212`, `:266`,
`:963`; `backend/open_webui/tasks.py:28`, `:69`; `backend/open_webui/utils/automations.py:64`,
`:69`). The events that remove stored sessions are listed in section 6.3; questions about how long
stored sessions are kept are security-sensitive (section 14).

What happens outside the person's own click:

| What | When | Where it runs | What people notice | Source |
|---|---|---|---|---|
| Provider registration | Once per server process, at start-up | Start-up | A provider with incomplete variables has no button; an unsupported `OAUTH_CODE_CHALLENGE_METHOD` stops the server | `backend/open_webui/config.py:2653-2782`; `backend/open_webui/main.py:524-525` |
| Start-up warnings | At start-up | Server log | Logout warning, SCIM provider warning, ignored sign-in parameters (section 10.3) | `backend/open_webui/config.py:2504-2513`, `:2624-2633`, `:2761-2779`; `backend/open_webui/env.py:911-916` |
| SCIM endpoints | Mounted at start-up only when `ENABLE_SCIM` is on | Start-up | Switching SCIM on or off needs a restart | `backend/open_webui/main.py:885-887` |
| Tool-server OAuth registrations | Loaded at start-up from `tool_server.connections`; a process that lacks one loads it at first use | In-process | An unreadable registration is skipped with a log line asking to reconnect the tool server | `backend/open_webui/main.py:621-656`; `backend/open_webui/utils/oauth.py:885-936` |
| Pruning stored SSO sessions | At each SSO sign-in, not in the background | During the callback | Beyond `OAUTH_MAX_SESSIONS_PER_USER` (code default 10) per person per provider, the oldest are removed; that browser loses provider sign-out and token forwarding (section 5.8) | `backend/open_webui/utils/oauth.py:2224-2235` |
| Replacing a tool-server connection | At each successful connection | During the callback | The person's previous connection to that tool server is replaced | `backend/open_webui/utils/oauth.py:1286-1296` |
| Refreshing a provider token (SSO) | On demand: when a feature needs the person's provider token and it is within five minutes of expiry (an ID token's own expiry counts too) | In the request that needs it. Requests made without a browser cookie (the code comment names automations and API calls) use the person's most recently updated stored session | A failed refresh deletes that stored session, and the feature gets no token until the next SSO sign-in; the MedIT GPT session is unaffected | `backend/open_webui/utils/oauth.py:1356-1419`, `:1448-1529`; `backend/open_webui/utils/middleware.py:3796-3829`; `backend/open_webui/functions.py:245-266` |
| Refreshing a tool-server token | On demand, when the token is within five minutes of expiry, including when the tool list loads | In the request | A failed refresh deletes the connection, and the tool shows as not connected (`Click to connect`) | `backend/open_webui/utils/oauth.py:1042-1080`; `backend/open_webui/routers/tools.py:134-171` |
| Removing unreadable stored sessions | Whenever a person's stored sessions are listed (sign-in pruning, a new tool-server connection, back-channel logout, token forwarding without a browser) | In the request | Sessions the server can no longer read, for example after a key change (section 7.5), are deleted with a log line (section 10.3) | `backend/open_webui/models/oauth_sessions.py:226-258` |
| Back-channel logout | When the identity provider sends a notice | In that request | Stored sessions deleted at once; MedIT GPT sessions end only with Redis (section 5.9) | `backend/open_webui/utils/oauth.py:2262-2447` |
| Event delivery (webhooks and Event functions) | After each change listed in section 9 | In-process tasks, so a slow webhook does not hold up the sign-in | None | `backend/open_webui/events.py:1062-1071`, `:1159-1171` |
| Disconnecting live connections | When a role changes (role mapping, role header, SCIM `active`), when SCIM deletes an account, and when back-channel logout revokes tokens (Redis only) | In-process | Open tabs reconnect; a longer gap shows `Connection lost. Reconnecting...` (section 9) | `backend/open_webui/events.py:1089-1100`; `backend/open_webui/socket/main.py:388-404`; `backend/open_webui/utils/auth.py:349-371` |
| Group mapping, group creation, profile pictures | During the SSO callback itself, not in the background; the picture is fetched while the person waits | In the request | None unless something fails (section 10.3) | `backend/open_webui/utils/oauth.py:1802-1848`, `:2027-2165` |
| Round-trip state (`owui-session`) | For the length of a sign-in round trip | The cookie itself, or Redis with `ENABLE_STAR_SESSIONS_MIDDLEWARE=True` | A lost or expired cookie makes the callback fail with the password message (section 5.2, step 4) | `backend/open_webui/main.py:2649-2674` |
| **Auto Redirect** and the session-expiry check | On each visit to `/auth`; the expiry check runs regularly in open tabs (`authentication-and-sign-in.md`) | In the **browser**, not on the server | Forwarding to the provider; `Session expired. Please sign in again.` | `src/routes/auth/+page.svelte:176-195`; `src/routes/+layout.svelte:931-950` |

Saving the **OAuth / OIDC** section writes the settings at once (`Config.upsert`), subject to
section 7.1; nothing is queued (`backend/open_webui/routers/auths.py:1513`). SCIM and admin changes
to roles and groups also take effect at once, in the request that makes them.

## 9. Notifications and Emails

**No email.** The application sends no email (ground truth). In this area that means: no message
when an account is created by SSO, a trusted header or SCIM; none when role or group mapping
changes someone's role or groups; and none to admins when a new person signs in by SSO. New
`pending` SSO accounts are found only in the admin user list or through an event webhook (below).
The in-app notification channel is not used for any event in this area
(`backend/open_webui/events.py:669-675`, `:1083-1087`).

**Pop-ups (toasts).** Every pop-up in this area is listed in section 10. The successful ones are
`You're now logged in.`, `OAuth session disconnected`, `Settings saved successfully!` and
`Reconnected`.

**Events.** Each change below is published to every configured event webhook that subscribes to it
and to any active Event function (`backend/open_webui/events.py:1171-1202`; event webhooks are
documented in `notifications-webhooks-events-and-banners.md`).

| Event | Webhook message | Published when (source recorded) | Source |
|---|---|---|---|
| `auth.login` | `User logged in` | Every successful SSO sign-in (`oauth`, with the provider), trusted-header sign-in (`trusted_header`) and token exchange (`oauth`) | `backend/open_webui/events.py:102-104`; `backend/open_webui/utils/oauth.py:2200-2208`; `backend/open_webui/routers/auths.py:210-218`, `:831`, `:1771` |
| `auth.logout` | `User logged out` | Sign-out; when the browser held a stored SSO session the source is `oauth`, with the provider | `backend/open_webui/events.py:105-107`; `backend/open_webui/routers/auths.py:970-984` |
| `auth.oauth_session.deleted` | `OAuth session deleted` | A person used **Disconnect OAuth** on a tool server. Pruning, failed refreshes and back-channel logout delete stored sessions without this event | `backend/open_webui/events.py:117-119`; `backend/open_webui/routers/auths.py:1085-1092` |
| `user.created` | `User created` | A new account from SSO (`oauth`, with role and provider), a trusted header (`trusted_header`) or SCIM (`scim`, with email, role and external ID) | `backend/open_webui/events.py:120-122`; `backend/open_webui/utils/oauth.py:2139-2146`; `backend/open_webui/routers/auths.py:887-894`; `backend/open_webui/routers/scim.py:644-654` |
| `user.updated` | `User updated` | **Update Name**, **Update Email** or **Update Picture** changed something at SSO sign-in (`oauth`), or SCIM changed profile fields (`scim`) | `backend/open_webui/events.py:123-125`; `backend/open_webui/utils/oauth.py:2084-2092`; `backend/open_webui/routers/scim.py:718-725`, `:821-828` |
| `user.role_updated` | `User role updated` | Role mapping at SSO sign-in or token exchange (`oauth`), the role header (`trusted_header`), or SCIM's `active` flag (`scim`) | `backend/open_webui/events.py:129-131`; `backend/open_webui/utils/oauth.py:1636-1643`; `backend/open_webui/routers/auths.py:777-784`; `backend/open_webui/routers/scim.py:727-734`, `:830-837` |
| `user.deleted` | `User deleted` | SCIM deleted an account (`scim`; the data includes the email) | `backend/open_webui/events.py:126-128`; `backend/open_webui/routers/scim.py:864-870` |
| `group.created` | `Group created` | **Auto-Create Groups** created a group (`oauth`), or SCIM did (`scim`) | `backend/open_webui/events.py:146-148`; `backend/open_webui/utils/oauth.py:1708-1714`; `backend/open_webui/routers/scim.py:989-995` |
| `group.updated` | `Group updated` | SCIM replaced or patched a group | `backend/open_webui/events.py:149-151`; `backend/open_webui/routers/scim.py:1051-1057`, `:1143-1149` |
| `group.deleted` | `Group deleted` | SCIM deleted a group | `backend/open_webui/events.py:152-154`; `backend/open_webui/routers/scim.py:1192-1198` |
| `group.member_added` | `Group member added` | Group mapping added the person (`oauth`), or SCIM added members (`scim`) | `backend/open_webui/events.py:155-157`; `backend/open_webui/utils/oauth.py:1776-1784`; `backend/open_webui/routers/scim.py:996-1003`, `:1058-1065`, `:1150-1157` |
| `group.member_removed` | `Group member removed` | Group mapping removed the person (`oauth`), or SCIM removed members (`scim`) | `backend/open_webui/events.py:158-160`; `backend/open_webui/utils/oauth.py:1739-1747`; `backend/open_webui/routers/scim.py:1066-1073`, `:1158-1165` |

Trusted-header group changes publish no event (`backend/open_webui/routers/auths.py:763-768`;
`backend/open_webui/models/groups.py:516-572`). Webhook messages have the subject's id appended in
brackets and are sent under the product name (`WEBUI_NAME`, `MedIT GPT` by default)
(`backend/open_webui/events.py:1034-1044`). Event payloads name people and so are personal data
(section 6.6; `authentication-and-sign-in.md`). Which webhooks production has is **TO BE
CONFIRMED**; an admin can use a `user.role_updated` or `group.member_removed` delivery, with its
source, to explain an unexpected role or group change (section 11).

**Live connection.** A role change or a SCIM deletion disconnects all of the person's live
connections (`backend/open_webui/events.py:1089-1100`), and so does back-channel logout when Redis
is configured (`backend/open_webui/utils/auth.py:349-371`). Open tabs reconnect by themselves;
when that takes longer than about two seconds on a visible page the app shows
`Connection lost. Reconnecting...` and then `Reconnected`
(`src/routes/+layout.svelte:162`, `:194`). After a back-channel logout the person's next action
ends in `Session expired. Please sign in again.` instead (section 5.9).

**Browser notifications.** None in this area.

**Messages to the identity provider.** Back-channel logout answers and SCIM answers go to the
identity provider's systems, not to people; their texts are in section 10.1.

## 10. Error, Warning and Notice Messages (Verbatim)

How server text reaches people in this area:

- **SSO callback failures** redirect to `/auth?error=<text>`, and the sign-in page shows the text
  unchanged in a red pop-up (`backend/open_webui/utils/oauth.py:2175-2181`;
  `src/routes/auth/+page.svelte:168-171`).
- **Trusted-header failures** appear as a red pop-up on the sign-in page, which prints the server's
  text (`src/routes/auth/+page.svelte:73-77`, `:199-200`).
- **Tool-server connections** that fail on the way back land on `/?error=<text>` and show a red
  pop-up on the home page (`backend/open_webui/utils/oauth.py:1318-1324`;
  `src/routes/(app)/+page.svelte:8-12`). Failures on the way out show the server's bare answer as a
  page, for example `{"detail":"Failed to re-register OAuth client"}`, because the browser opened
  the address directly (`src/lib/apis/configs/index.ts:568-576`).
- **Token exchange, SCIM and back-channel logout** answer programs and the identity provider;
  people see nothing.

Placeholders are written `{name}` using the source's variable name.

### 10.1 Messages from the Server

**Single sign-on (shown on `/auth` as a red pop-up)**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The email or password provided is incorrect. Please check for typos and try logging in again.` | Error (HTTP 400, shown after a redirect) | `backend/open_webui/constants.py:60`; raised at `backend/open_webui/utils/oauth.py:1911`, `:1920`, `:1943`, `:1953`, `:1988`, `:1991`, `:1994`, `:1999`, `:2008` | SSO only, although no password was typed: the code exchange failed (sign-in cancelled or refused at the provider, the round-trip cookie lost, the code reused, a wrong client secret, the provider unreachable); no user details; no subject claim; no email claim (or no GitHub primary email); the email domain is not in **Allowed Domains** | Try once more from the button, in one tab, without using Back; if it repeats, note the time and the button used | The server log line for that time names the real cause (section 10.3); follow 11.1 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403, shown after a redirect) | `backend/open_webui/constants.py:70-72`; `backend/open_webui/utils/oauth.py:1600-1608`, `:2148-2152` | No account matches and **OAuth Signup** is off (this includes an account with the same email while **Merge Accounts by Email** is off); or **Role Mapping** is on and the roles claim matches no **Allowed Roles** or **Admin Roles** value | Ask for access through the organization's process (**TO BE CONFIRMED**) | Follow 11.2 |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400, shown after a redirect) | `backend/open_webui/constants.py:46`; `backend/open_webui/utils/oauth.py:2095-2099` | **OAuth Signup** is on, no account carries this provider's subject, an account with the same email exists (password, LDAP, SCIM, trusted-header or another provider), and **Merge Accounts by Email** is off | Sign in the way the account was created | Follow 11.3; linking accounts is an admin and policy decision |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500, shown after a redirect) | `backend/open_webui/constants.py:43`; `backend/open_webui/utils/oauth.py:2127-2128` | The new SSO account could not be stored | Try again later | Escalate with the time; the database may be unavailable |
| `[ERROR: Error during OAuth process]` | Error (shown after a redirect) | `backend/open_webui/utils/oauth.py:2167-2173`; `backend/open_webui/constants.py:16-23` | Any other failure during the callback, for example a database error or a failure while applying group mapping | Try once more; note the time | Escalate; the log line `Error during OAuth process: {e}` gives the cause |
| `{"detail":"Not Found"}` | Error page (HTTP 404; the framework's default text) | `backend/open_webui/utils/oauth.py:1851-1859`, `:1874-1877` | Starting SSO, or returning from the provider, while **OAuth / OIDC** is off in the server process that answered, or for a provider that is not registered | Use the sign-in method the organization provides | Ask the maintainer whether SSO is meant to be on and which providers are registered (`oauth.providers` in `/api/config`) |
| `Internal Server Error` | Error page (HTTP 500; the framework's default text) | `backend/open_webui/utils/oauth.py:1870` (no handler) | Starting SSO while the provider's discovery document cannot be fetched. Read from the code, not exercised | Try later | Escalate: provider or network outage |

**Trusted headers, sign-out and disconnecting**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Your provider has not provided a trusted header. Please contact your administrator for assistance.` | Error (HTTP 400), pop-up on the sign-in page; the spinner stays | `backend/open_webui/constants.py:63-65`; `backend/open_webui/routers/auths.py:733-735` | Trusted-header mode, but the request arrived without the email header (the proxy did not add it, or the request did not pass through the proxy) | Reload; sign in to the proxy again | Follow 11.13 |
| `The email or password provided is incorrect. Please check for typos and try logging in again.` | Error (HTTP 400), pop-up on the sign-in page | `backend/open_webui/routers/auths.py:829-833`; `backend/open_webui/models/auths.py:178-194` | Trusted-header mode: the account with the header's email has no active sign-in record, for example a SCIM-created account | None | Follow 11.9 |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403), pop-up on the sign-in page | `backend/open_webui/constants.py:73`; `backend/open_webui/routers/auths.py:724-728` | Trusted-header sign-in while `ENABLE_PASSWORD_AUTH=False` (the same switch refuses password sign-in) | None | Escalate: server configuration |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500), pop-up on the sign-in page | `backend/open_webui/routers/auths.py:871-872`, reached from `:747-759` | First trusted-header sign-in: the new account could not be stored | Try again later | Escalate with the time |
| `User mismatch. Please sign in again.` | Error (HTTP 401); the browser then ends the session | `backend/open_webui/utils/auth.py:462-468` | Trusted-header mode: the proxy now reports a different email from the session's account, for example after someone else signed in to the proxy on a shared computer | Sign out, close the browser, sign in again | Follow 11.14 |
| `Failed to sign out from the OpenID provider.` | Error (HTTP 500); nothing visible from the user menu | `backend/open_webui/routers/auths.py:1038-1047` | **Sign Out** of an SSO session when the provider's discovery document cannot be read | Close the browser; sign out at the provider's own site if needed | Follow 11.7 |
| `No OAuth session found for this provider` | Error (HTTP 404), red pop-up in the chat composer | `backend/open_webui/routers/auths.py:1079-1083`; shown by `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:615-616` | **Disconnect OAuth** when the person has no stored connection to that tool server (already removed) | Reload the page | None needed |

**Tool-server connections (MCP)**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `OAuth callback failed: {detail}` | Error, pop-up on the home page | `backend/open_webui/utils/oauth.py:282-310`, `:1305-1306`, `:1321-1324` | The connection round trip failed. `{detail}` is one of the next six texts, or the tool's sign-in service's own error; the whole message is cut at 200 characters with `...` | Click the amber tool chip to connect again | If it repeats, escalate with the tool name, the full text and the time |
| `OAuth callback state is invalid or expired` | Error (as `{detail}` above) | `backend/open_webui/utils/oauth.py:1246-1250` | The round trip's saved state was missing or had expired, for example the connection was started in another tab or browser | Start again from the same tab | None |
| `OAuth callback user is not authorized` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:1252-1256` | The account that started the connection is no longer `user` or `admin` (for example it was set to `pending` meanwhile) | Contact an admin | Check the account's role with an admin |
| `OAuth callback user does not match authenticated session` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:1258-1263` | A different MedIT GPT account is signed in in this browser from the one that started the connection | Sign in as the right account and connect again | None |
| `Missing state parameter in callback (session may have expired)` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:296-299` | The tool's service returned without the state value | Connect again | Escalate if it repeats |
| `Missing expected key '{missing}' in OAuth response` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:300-301` | The tool's service answered without a required value | None | Escalate: tool-server configuration |
| `Upstream provider returned {e.status}: {e.message}` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:292-293` | The tool's service answered with an HTTP error | Try later | Escalate if it persists |
| `Token exchange failed: {error_desc}` | Error, pop-up on the home page | `backend/open_webui/utils/oauth.py:1274-1280` | The tool's service refused to issue a token; `{error_desc}` is its reason | Try again | Escalate with the full text; the tool-server registration may be wrong |
| `Failed to store OAuth session server-side` | Error, pop-up on the home page | `backend/open_webui/utils/oauth.py:1298-1300` | The connection worked but could not be saved | Try again | Escalate: database |
| `Failed to obtain OAuth token` | Error, pop-up on the home page | `backend/open_webui/utils/oauth.py:1301-1304` | The tool's service returned no token | Try again | Escalate |
| `OAuth authorization endpoint could not be resolved for this client. Re-register the MCP server; its OAuth discovery documents may be missing or unreachable.` | Error page (HTTP 400) | `backend/open_webui/utils/oauth.py:1219-1232` | Starting a connection to a tool server whose sign-in address is unknown | None | Escalate to the admin who manages the tool server |
| `OAuth authorization state was not generated` | Error page (HTTP 500) | `backend/open_webui/utils/oauth.py:1211-1215` | Internal failure while starting a connection | Try again | Escalate |
| `Failed to re-register OAuth client` | Error page (HTTP 500) | `backend/open_webui/main.py:2785-2796` | The tool's service rejected MedIT GPT's registration and automatic re-registration failed | None | Escalate to the tool-server admin; the log names the cause (section 10.3) |
| `OAuth client unavailable after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2798-2804` | Re-registration reported success but the registration could not be loaded | None | Escalate |
| `OAuth client registration is still invalid after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2806-2810` | The tool's service still rejects the registration after re-registration | None | Escalate to the tool-server admin |
| `{"detail":"Not Found"}` | Error page (HTTP 404) | `backend/open_webui/main.py:2780-2783`; `backend/open_webui/utils/oauth.py:1195-1203`, `:1235-1237` | The tool server's connection details cannot be loaded: it was removed, it is not an OAuth tool server, or its stored registration is unreadable (the log then asks to reconnect the tool server) | None | Follow 11.17 |
| `Failed to register OAuth client: {e}` | Error (HTTP 400); the admin's tool-server dialog shows only its own `Registration failed` (section 10.2), so this text is visible in the browser's developer tools or the log | `backend/open_webui/routers/configs.py:172-209`; `src/lib/components/AddToolServerModal.svelte:143-146` | An admin registering an OAuth tool server; `{e}` carries one of the next four texts | Admin only | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Could not discover the OAuth authorization server metadata (authorization_endpoint) for {oauth_server_url}. The MCP server must expose RFC 8414 / RFC 9728 discovery documents so Open WebUI can resolve where to send users to authorize.` | Error (inside the message above, or in the re-registration log line) | `backend/open_webui/utils/oauth.py:576-583` | The tool server does not publish where people should sign in | Admin only | As above |
| `Dynamic client registration failed: {error_text}` | Error (as above) | `backend/open_webui/utils/oauth.py:636-640` | The tool's service refused automatic registration and gave a reason | Admin only | As above |
| `Error parsing client registration response` | Error (as above) | `backend/open_webui/utils/oauth.py:636-640` | The registration answer could not be read and carried no text | Admin only | As above |
| `Dynamic client registration failed` | Error (as above) | `backend/open_webui/utils/oauth.py:641` | Registration ended without an answer. *Corrected 2026-10-10: unreachable in v0.11.4; the registration address is always set (`backend/open_webui/utils/oauth.py:585-590`) and the request block always returns or raises before this line (`:600-640`); a connection failure raises the HTTP library's own error instead.* | Admin only | As above |

**Token exchange (answers to the calling program)**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Token exchange is disabled` | Error (HTTP 403) | `backend/open_webui/routers/auths.py:1636-1640` | `ENABLE_OAUTH_TOKEN_EXCHANGE` is off (code default) | Use the web sign-in | Expected unless the maintainer enabled the feature |
| `API rate limit exceeded` | Error (HTTP 429) | `backend/open_webui/constants.py:87`; `backend/open_webui/routers/auths.py:1642-1648` | The optional token-exchange limit was reached | Wait for the window to pass | None |
| `Provider '{name}' is not configured` | Error (HTTP 404) | `backend/open_webui/constants.py:132`; `backend/open_webui/routers/auths.py:1650-1665` | The provider named in the address is not registered (`{name}` is the lower-cased provider) | Use a registered provider name | Section 7.4 |
| `Unable to determine which client the token was issued to` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1667-1673` | Trusted client IDs are set but the provider would not say which client the token belongs to | None | Escalate to the maintainer |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/auths.py:1674-1679`, `:1720-1730`; `backend/open_webui/utils/oauth.py:1576-1578`, `:1600-1608` | A token issued to an untrusted client; an email domain not in **Allowed Domains**; with role mapping on, no readable roles claim (and no `*` in **Allowed Roles**) or roles matching nothing | None | Escalate to the maintainer |
| `Invalid token or unable to validate with provider` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1682-1696` | The provider did not accept the token (for example expired, or from another provider) or could not be reached. The similar text `Invalid token or unable to fetch user info` in the same block is replaced by this one before it is sent | Obtain a fresh token | None |
| `Token missing required 'sub' claim` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1700-1709` | The provider returned no subject for the token | None | Escalate |
| `Token missing required email claim` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1711-1718` | The provider returned no email (in **Email Claim**) for the token | None | Escalate |
| `User not found. Please sign in via the web interface first.` | Error (HTTP 403) | `backend/open_webui/routers/auths.py:1732-1752` | No account carries the token's subject (or, with merge on, its email); token exchange never creates accounts | Sign in once through the website | Section 5.12 |

**SCIM (answers to the identity provider's SCIM client)**

When SCIM is off the paths do not exist and every request gets the framework's 404. Most answers
below use the framework's `{"detail": …}` shape; `User {user_id} not found` from a single-user read
and the patch-validation texts use the SCIM error format (`backend/open_webui/routers/scim.py:48-65`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Authorization header required` | Error (HTTP 401) | `backend/open_webui/routers/scim.py:237-242` | The SCIM client sent no credentials | Not applicable | The identity provider team checks its SCIM connection |
| `Invalid authorization format. Expected: Bearer <token>` | Error (HTTP 401) | `backend/open_webui/routers/scim.py:244-250` | The credentials were not in the form `Bearer` plus the token | Not applicable | As above |
| `Invalid authentication scheme` | Error (HTTP 401) | `backend/open_webui/routers/scim.py:252-257` | A scheme other than `Bearer` | Not applicable | As above |
| `SCIM is not enabled` | Error (HTTP 403) | `backend/open_webui/routers/scim.py:259-267` | SCIM switched off for a mounted router; not expected, because the router is mounted only when SCIM is on | Not applicable | None |
| `Invalid SCIM token` | Error (HTTP 401) | `backend/open_webui/routers/scim.py:269-276` | The token does not match `SCIM_TOKEN`, or `SCIM_TOKEN` is empty | Not applicable | Escalate to the maintainer; never ask for or copy the token |
| `Authentication failed` | Error (HTTP 401) | `backend/open_webui/routers/scim.py:282-290` | An unexpected error while checking the credentials | Not applicable | Escalate |
| `SCIM_AUTH_PROVIDER environment variable is required when SCIM is enabled` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:306-316` | An external-ID lookup or write while `SCIM_AUTH_PROVIDER` is empty (the trap in section 5.11) | Not applicable | Escalate: server configuration |
| `User {user_id} not found` | Error (HTTP 404) | `backend/open_webui/routers/scim.py:566-568`, `:668-673`, `:748-753`, `:850-855` | The ID is unknown, or belongs to an account SCIM cannot see (no SSO link and not SCIM-created) | Not applicable | Section 5.11 |
| `User with externalId {user_data.externalId} already exists` | Error (HTTP 409) | `backend/open_webui/routers/scim.py:581-588` | Creating an account whose external ID (or matching SSO subject) is already taken | Not applicable | As above |
| `User with email {email} already exists` | Error (HTTP 409) | `backend/open_webui/routers/scim.py:598-604` | Creating an account whose email already has an account | Not applicable | Section 5.11 (configuration trap) |
| `Failed to create user` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:631-635` | The account could not be stored | Not applicable | Escalate |
| `Failed to stamp SCIM user` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:637-642` | The account was stored but could not be marked as SCIM-managed | Not applicable | Escalate; an unmarked account is invisible to SCIM |
| `Failed to update user` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:701-706`, `:810-815` | A replace or patch could not be stored | Not applicable | Escalate |
| `Failed to delete user` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:857-862` | The account (or its chats) could not be deleted | Not applicable | Escalate |
| `Unsupported PATCH operation: {operation.op}` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:767-768` | A user patch other than `add`, `replace` or `remove` | Not applicable | As above |
| `Remove requires a path` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:769-771` | A `remove` without a path | Not applicable | As above |
| `Removing {path} is not supported` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:772-773` | Removing anything other than `externalId` | Not applicable | As above |
| `A pathless operation requires an attribute object` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:775-777` | A patch without a path and without an attribute object | Not applicable | As above |
| `active must be a boolean` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:783-785` | `active` sent as something other than true or false | Not applicable | As above |
| `{path} must be a string` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:789-791` | A name or email patch with a value that is not text | Not applicable | As above |
| `externalId must be a string or null` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:793-795` | An external-ID patch with another kind of value | Not applicable | As above |
| `Unsupported PATCH path: {path}` | Error (HTTP 400) | `backend/open_webui/routers/scim.py:800-801` | A user patch to any attribute other than `active`, `userName`, `displayName`, `emails[primary eq true].value`, `name.formatted` or `externalId` | Not applicable | As above |
| `Group {group_id} not found` | Error (HTTP 404) | `backend/open_webui/routers/scim.py:928-933`, `:1017-1022`, `:1087-1092`, `:1178-1183` | The group ID is unknown | Not applicable | As above |
| `No admin user found` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:960-966` | Creating a group while no admin account exists | Not applicable | Escalate |
| `Failed to create group` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:968-973` | The group could not be stored | Not applicable | Escalate |
| `Failed to update group` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:1044-1049`, `:1136-1141` | A group replace or patch could not be stored | Not applicable | Escalate |
| `Failed to delete group` | Error (HTTP 500) | `backend/open_webui/routers/scim.py:1185-1190` | The group could not be deleted | Not applicable | Escalate |

**Back-channel logout (answers to the identity provider, as `error_description` with HTTP 400)**

When the feature is off the endpoint answers 404 (`backend/open_webui/main.py:2863-2864`). None of
these is seen by people; the triggers are summarized rather than detailed.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Missing logout_token parameter` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2271-2282` | The notice carried no logout token | Not applicable | The identity provider team checks its back-channel set-up |
| `Malformed logout_token` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2284-2293` | The logout token could not be read | Not applicable | As above |
| `logout_token missing iss claim` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2295-2299` | The token does not say who issued it | Not applicable | As above |
| `No configured provider matches token issuer` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2301-2331` | The issuer is not one of the registered providers | Not applicable | Compare with section 7.4 |
| `Invalid logout_token: {e}` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2333-2366` | The notice failed the server's authenticity checks; `{e}` names the failed check | Not applicable | Escalate to the maintainer |
| `Failed to validate logout_token` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2367-2372` | An unexpected error during those checks | Not applicable | Escalate |
| `Missing backchannel-logout event claim` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2374-2381` | The token does not declare itself a back-channel logout notice | Not applicable | As above |
| `logout_token must not contain nonce` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2383-2389` | The token carries a value the standard forbids in logout notices | Not applicable | As above |
| `logout_token must contain sub or sid` | Error (HTTP 400) | `backend/open_webui/utils/oauth.py:2391-2400` | The token names neither a person nor a provider session | Not applicable | As above |

### 10.2 Messages from the Browser

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You're now logged in.` | Success | `src/routes/auth/+page.svelte:50` | Any successful sign-in, including the return from SSO and trusted-header sign-in | None | None |
| `Signing in to {{WEBUI_NAME}}` | Notice, with a spinner (shows "Signing in to MedIT GPT") | `src/routes/auth/+page.svelte:235-248` | Trusted-header mode (and no-login mode) | Wait; if it never finishes, see 11.13 | None |
| `Continue with {{provider}}` | Button label | `src/routes/auth/+page.svelte:491`, `:521`, `:543`, `:569-573`, `:583` | One button per registered provider; `{{provider}}` is Google, Microsoft, GitHub, the OIDC display name (`SSO` by default) or Feishu | Choose the organization's provider | Which provider production shows is TO BE CONFIRMED |
| `These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.` | Notice (yellow), admins only | `src/lib/components/admin/Settings/Authentication.svelte:550-558` | The **OAuth / OIDC** section while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off; `{{ENV_VAR}}` shows that variable's name | Admins change these settings through the server environment | Section 7.1 |
| `Settings saved successfully!` | Success | `src/lib/components/admin/Settings/Authentication.svelte:98-107` | Every part of the Authentication tab saved | None | Section 7.3 explains which saved values take effect |
| `Please connect all required integrations before sending a message` | Warning | `src/lib/components/chat/Chat.svelte:3130-3133` | Sending while a model's default tool still needs connecting | Click the amber tool chip | Follow 11.17 |
| `Click to connect` | Tooltip | `src/lib/components/chat/MessageInput.svelte:2546-2559` | The amber chip of each tool that needs connecting | Click it | None |
| `Disconnect OAuth` | Tooltip | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:592-596` | Beside a connected MCP tool server in the integrations menu | None | None |
| `OAuth session disconnected` | Success | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:608-610` | After **Disconnect OAuth** | None | None |
| `Failed to disconnect` | Error | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:615-616` | Disconnecting failed without a server text (otherwise the server's text appears, such as `No OAuth session found for this provider`) | Reload and try again | Escalate if it repeats |
| `An unknown error occurred.` | Error | `src/routes/(app)/+page.svelte:8-12` | Fallback for an empty `?error=` on the home page; the surrounding check makes it unreachable in practice | None | None |
| `Session expired. Please sign in again.` | Error | `src/routes/+layout.svelte:931-950` | The browser ended a session the server refused, for example after `User mismatch. Please sign in again.` or a back-channel logout with Redis (`authentication-and-sign-in.md`) | Sign in again | None, unless it repeats |
| `Connection lost. Reconnecting...` | Warning | `src/routes/+layout.svelte:162` | The live connection dropped for more than a moment, for example after a role change | Wait | None |
| `Reconnected` | Success | `src/routes/+layout.svelte:192-194` | The live connection came back after the warning above | None | None |
| `Please enter Client ID and Client Secret` | Error, admins only | `src/lib/components/AddToolServerModal.svelte:120-123` | Registering an **OAuth 2.1 (Static)** tool server without both values | Fill in both | Tools document |
| `Registration failed` | Error, admins only | `src/lib/components/AddToolServerModal.svelte:143-146` | Registering an OAuth tool server failed; the server's reason (`Failed to register OAuth client: {e}`) is not shown | Check the tool server's address and sign-in settings | Tools document |
| `Registration successful` | Success, admins only | `src/lib/components/AddToolServerModal.svelte:148-154` | Registration worked | Save the connection | None |
| `Please save the connection to persist the OAuth client information and do not change the ID` | Warning, admins only | `src/lib/components/AddToolServerModal.svelte:148-153` | Shown with the success message: the registration is kept only when the connection is saved | Save without changing the ID | Explains connections that ask to register again |
| `OAuth ID` | Label, admins only | `src/lib/components/admin/Users/UserList/EditUserModal.svelte:186-198` | Admin user editor, for an account linked to an SSO provider; lists provider names and subject identifiers | None | Personal identifiers: do not copy into tickets unless asked by the maintainer |

### 10.3 Server Log Lines (Not Shown to Users)

Logs go to standard output (ground truth). Several lines contain personal data (section 6.6).

**Single sign-on**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `OAuth callback error during authorize_access_token for provider {provider}: {detailed_error}` | Log (warning) | `backend/open_webui/utils/oauth.py:1912-1920` | Behind the password message when the code exchange fails; `{detailed_error}` begins `OAuth callback failed:` and gives the provider's own error, a missing-state note, or an upstream HTTP status | None | The maintainer matches the time of the attempt |
| `OAuth callback error during authorize_access_token retry for provider {provider}: {detailed_error}` | Log (warning) | `backend/open_webui/utils/oauth.py:1903-1911` | The retry after refreshing the provider's signing keys also failed | None | As above |
| `OIDC bad_signature for provider {provider} — evicting cached JWKS and retrying` | Log (warning) | `backend/open_webui/utils/oauth.py:1891-1900` | The provider's signature did not match the cached keys, which the code comment attributes to the provider changing its signing keys; the server fetches fresh keys and retries once | None | Informational unless followed by the retry line above |
| `OAuth callback failed for provider {provider}, user data is missing` | Log (warning) | `backend/open_webui/utils/oauth.py:1941-1943` | No user details from the provider | None | Escalate: provider configuration |
| `OAuth callback failed, sub is missing: {user_data}` | Log (warning) | `backend/open_webui/utils/oauth.py:1951-1953` | No subject claim; `{user_data}` is the provider's full claim set (personal data) | None | Check **Sub Claim** with the maintainer |
| `No primary email found in GitHub response` | Log (warning) | `backend/open_webui/utils/oauth.py:1987-1988` | GitHub sign-in without a primary email | None | Not expected for this deployment unless GitHub is registered |
| `Failed to fetch GitHub email` | Log (warning) | `backend/open_webui/utils/oauth.py:1989-1991` | GitHub refused the email lookup | None | As above |
| `Error fetching GitHub email: {e}` | Log (warning) | `backend/open_webui/utils/oauth.py:1992-1994` | The GitHub email lookup failed | None | As above |
| `OAuth callback failed, email is missing: {user_data}` | Log (warning) | `backend/open_webui/utils/oauth.py:1997-1999` | No email claim and no fallback (personal data) | None | Check **Email Claim** with the maintainer |
| `OAuth callback failed, e-mail domain is not in the list of allowed domains: {user_data}` | Log (warning) | `backend/open_webui/utils/oauth.py:2002-2008` | The domain is not in **Allowed Domains** (personal data) | None | Compare the domain with **Allowed Domains**, letter case included |
| `OAuth role management enabled but user roles do not match any allowed/admin roles. User roles: {oauth_roles}, allowed: {oauth_allowed_roles}, admin: {oauth_admin_roles}` | Log (warning) | `backend/open_webui/utils/oauth.py:1600-1604` | Role mapping refused the sign-in; names the roles received | None | Compare with **Allowed Roles** and **Admin Roles** |
| `Username claim is missing, using email as name` | Log (warning) | `backend/open_webui/utils/oauth.py:2112-2115` | A new SSO account was named after its email | None | Check **Username Claim** |
| `Cannot update email to {new_email} for user {user.id} because it is already taken.` | Log (error) | `backend/open_webui/utils/oauth.py:2054-2058` | **Update Email** found another account using the new address (personal data) | None | Escalate if the person reports an outdated email |
| `Error during OAuth process: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:2167-2168` | Every callback failure, with its cause | None | Escalate with the time |
| `Failed to create OAuth session for user {user.id}, provider {provider}` | Log (warning) | `backend/open_webui/utils/oauth.py:2255-2256` | Signed in, but the stored SSO session was not created; provider sign-out and token forwarding will not work for that sign-in | None | Escalate if it repeats |
| `Failed to store OAuth session server-side: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:2257-2258` (SSO), `:1298-1300` (tool server) | As above, with the error; for a tool server, the connection fails with the pop-up of the same name | None | Escalate |
| `Group '{group_name}' not found via OAuth claim. Creating group...` | Log (info) | `backend/open_webui/utils/oauth.py:1686-1688` | **Auto-Create Groups** is creating a group named in the claim | None | Explains new groups appearing |
| `Failed to create group '{group_name}' via OAuth.` | Log (error) | `backend/open_webui/utils/oauth.py:1715-1716` | Group creation returned nothing | None | Escalate |
| `Error creating group '{group_name}' via OAuth: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:1717-1718` | Group creation failed | None | Escalate |
| `Rejected OAuth profile picture from {picture_url}: MIME {upstream_mime!r} is not allowed` | Log (warning) | `backend/open_webui/utils/oauth.py:1837-1842` | The picture is not an allowed image type; `/user.png` is used | None | Explains a default picture |
| `Failed to fetch profile picture from {picture_url}` | Log (warning) | `backend/open_webui/utils/oauth.py:1843-1845` | The picture address answered with an error; `/user.png` is used | None | As above |
| `Error processing profile picture '{picture_url}': {e}` | Log (error) | `backend/open_webui/utils/oauth.py:1846-1848` | The picture could not be fetched or checked; `/user.png` is used | None | As above |

**Provider tokens and stored sessions**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Token refresh failed for user {user_id}, provider {session.provider}, deleting session {session.id}` | Log (warning) | `backend/open_webui/utils/oauth.py:1404-1414` | An SSO provider token could not be refreshed; the stored session is deleted | None | Token forwarding resumes after the next SSO sign-in |
| `Token refresh failed for user {user_id}, client_id {session.provider}, deleting session {session.id}` | Log (warning) | `backend/open_webui/utils/oauth.py:1066-1075` | A tool-server token could not be refreshed; the connection is deleted and the tool asks to connect again | None | Follow 11.17 |
| `No refresh token available for session {session.id}` | Log (warning) | `backend/open_webui/utils/oauth.py:1123-1125`, `:1462-1464` | The provider or tool service issued no refresh token, so the token cannot be renewed | None | Expected with some providers; escalate if connections drop often |
| `Token refresh failed for provider {provider}: {r.status} - {error_text}` | Log (error) | `backend/open_webui/utils/oauth.py:1522-1525` | The SSO provider refused the refresh | None | As above |
| `Token refresh failed for client_id {client_id}: {r.status} - {error_text}` | Log (error) | `backend/open_webui/utils/oauth.py:1185-1188` | The tool's service refused the refresh | None | As above |
| `No OAuth session found for user {user_id}, session {session_id}` | Log (warning) | `backend/open_webui/utils/oauth.py:1370-1373` | A feature needed the person's SSO token but the browser's stored session no longer exists | None | Ask the person to sign out and sign in by SSO |
| `No OAuth session found for user {user_id}, client_id {client_id}` | Log (warning) | `backend/open_webui/utils/oauth.py:1056-1059` | The person has no connection to that tool server | None | The tool shows `Click to connect` |
| `OAuth token response missing both 'expires_in' and 'expires_at'; defaulting to {DEFAULT_TOKEN_EXPIRY_SECONDS}s from now` | Log (warning) | `backend/open_webui/utils/oauth.py:234-239` | The provider gave no expiry but a refresh token; one hour (3,600 seconds) is assumed | None | Informational |
| `Skipping OAuth session {session.id} due to decryption failure, deleting corrupted session: {type(e).__name__}: {e}` | Log (warning) | `backend/open_webui/models/oauth_sessions.py:247-252` | A stored session could not be read (for example after a key change, section 7.5) and was deleted | None | Escalate if many appear at once |

**Tool-server connections**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to lazily add OAuth client {expected_client_id} from config: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error) | `backend/open_webui/utils/oauth.py:921-927` | A server process could not read a tool server's stored registration on first use | None | The tool-server admin must reconnect the tool server; follow 11.17 |
| `Failed to lazily add OAuth client {expected_client_id} from config: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:928-934` | Any other failure loading the registration | None | Escalate to the tool-server admin |
| `Error adding OAuth client for MCP tool server {server_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error, at start-up) | `backend/open_webui/main.py:647-652` | As the first row, at start-up | None | As above |
| `Error adding OAuth client for MCP tool server {server_id}: {e}` | Log (error, at start-up) | `backend/open_webui/main.py:653-658` | Any other failure loading a registration at start-up | None | As above |
| `Detected invalid OAuth client {client_id}; attempting re-registration` | Log (info) | `backend/open_webui/main.py:2785-2789` | The tool's service rejected the registration when someone started connecting | None | Followed by success or by the next rows |
| `OAuth client preflight detected invalid registration for {client_info.client_id}: {error} {error_description}` | Log (warning) | `backend/open_webui/utils/oauth.py:1011-1015` | The check behind the row above, with the service's reason | None | As above |
| `OAuth client re-registration failed for {client_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error) | `backend/open_webui/main.py:734-740` | Re-registration could not read the stored registration | None | The tool-server admin must reconnect the tool server |
| `OAuth client re-registration failed for {client_id}: {e}` | Log (error) | `backend/open_webui/main.py:741-747` | Re-registration failed (for example the discovery or registration texts in section 10.1) | None | Escalate to the tool-server admin |
| `Unable to locate MCP tool server configuration for client {client_id} during re-registration` | Log (warning) | `backend/open_webui/main.py:2692-2694` | The tool server no longer exists in the settings | None | As above |
| `Failed to persist updated OAuth client info for tool server {client_id}: {e}` | Log (error) | `backend/open_webui/main.py:2759-2761` | The repaired registration could not be saved | None | Escalate |
| `Re-registered OAuth client {client_id} for tool server` | Log (info) | `backend/open_webui/main.py:2768` | Automatic re-registration succeeded | None | None |
| `OAuth authorize failed for client {client_id}: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:1219-1224` | Behind the authorization-endpoint error page in section 10.1 | None | As above |
| `Invalid token response for client_id {client_id}: {error_desc}` | Log (error) | `backend/open_webui/utils/oauth.py:1276-1279` | Behind `Token exchange failed: {error_desc}` | None | As above |
| `OAuth callback error for user_id={user_id} client_id={client_id}: {error_message}` | Log (warning) | `backend/open_webui/utils/oauth.py:1305-1313` | Behind every `OAuth callback failed: …` pop-up | None | The maintainer matches the time |

**Trusted headers, sign-out and token exchange**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Ignoring invalid trusted role header value: {trusted_role}` | Log (warning) | `backend/open_webui/routers/auths.py:784-785` | The role header held something other than `admin`, `user` or `pending`; the role is unchanged | None | Escalate: proxy configuration |
| `authenticate_user_by_email: {email}` | Log (info) | `backend/open_webui/models/auths.py:184` | Every trusted-header sign-in (personal data) | None | None |
| `OpenID signout error: {e}` | Log (error) | `backend/open_webui/routers/auths.py:1041-1042` | Behind `Failed to sign out from the OpenID provider.` | None | Escalate with the time |
| `Token exchange trusted-client check requires an introspection_endpoint` | Log (warning) | `backend/open_webui/routers/auths.py:1597-1600` | Trusted client IDs are set but the provider offers no token introspection | None | Escalate: configuration |
| `Token introspection returned {r.status}` | Log (warning) | `backend/open_webui/routers/auths.py:1609-1611` | The provider's introspection answered with an error | None | As above |
| `Token introspection reports the token is inactive` | Log (warning) | `backend/open_webui/routers/auths.py:1614-1616` | The token presented for exchange is no longer active | None | None |
| `Token introspection failed: {e}` | Log (warning) | `backend/open_webui/routers/auths.py:1619-1621` | Introspection could not be completed | None | As above |
| `Token exchange denied: token was issued to an untrusted client for {provider}` | Log (warning) | `backend/open_webui/routers/auths.py:1674-1679` | The token belongs to a client not in the trusted list | None | None |
| `Token exchange failed for provider {provider}: {e}` | Log (warning) | `backend/open_webui/routers/auths.py:1691-1696` | Behind `Invalid token or unable to validate with provider` | None | None |
| `Token exchange failed: sub claim missing from user data` | Log (warning) | `backend/open_webui/routers/auths.py:1704-1709` | Behind `Token missing required 'sub' claim` | None | None |
| `Token exchange failed: email claim missing from user data` | Log (warning) | `backend/open_webui/routers/auths.py:1713-1718` | Behind `Token missing required email claim` | None | None |
| `Token exchange denied: email domain not in allowed domains list` | Log (warning) | `backend/open_webui/routers/auths.py:1725-1730` | The email domain is not in **Allowed Domains** | None | None |
| `Token exchange denied: no readable roles claim in userinfo or the token` | Log (warning) | `backend/open_webui/utils/oauth.py:1576-1578` | Role mapping is on and the exchanged token carries no readable roles | None | None |

**SCIM, back-channel logout and start-up**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `SCIM auth check - raw ENABLE_SCIM: {enable_scim}, type: {type(enable_scim)}` | Log (info) | `backend/open_webui/routers/scim.py:260-261` | Every SCIM request | None | Shows SCIM traffic in the log |
| `SCIM authentication error: {e}` | Log (error) | `backend/open_webui/routers/scim.py:282-286` | Behind `Authentication failed` | None | Escalate |
| `Back-channel logout: cannot decode logout_token: {e}` | Log (warning) | `backend/open_webui/utils/oauth.py:2288-2293` | Behind `Malformed logout_token` | None | As section 10.1 |
| `Back-channel logout: no configured provider matches issuer {token_issuer}` | Log (warning) | `backend/open_webui/utils/oauth.py:2323-2331` | Behind `No configured provider matches token issuer` | None | As section 10.1 |
| `Back-channel logout: invalid logout_token: {e}` | Log (warning) | `backend/open_webui/utils/oauth.py:2361-2366` | Behind `Invalid logout_token: {e}` | None | As section 10.1 |
| `Back-channel logout: error validating logout_token: {e}` | Log (error) | `backend/open_webui/utils/oauth.py:2367-2372` | Behind `Failed to validate logout_token` | None | As section 10.1 |
| `Back-channel logout: missing required backchannel-logout event claim` | Log (warning) | `backend/open_webui/utils/oauth.py:2376-2381` | Behind `Missing backchannel-logout event claim` | None | As section 10.1 |
| `Back-channel logout: logout_token contains nonce (rejected per spec)` | Log (warning) | `backend/open_webui/utils/oauth.py:2384-2389` | Behind `logout_token must not contain nonce` | None | As section 10.1 |
| `Back-channel logout: logout_token contains neither sub nor sid` | Log (warning) | `backend/open_webui/utils/oauth.py:2395-2400` | Behind `logout_token must contain sub or sid` | None | As section 10.1 |
| `Back-channel logout: Redis not configured, cannot revoke JWT tokens. OAuth sessions will be deleted but existing JWTs will remain valid until expiry.` | Log (warning) | `backend/open_webui/utils/oauth.py:2418-2424` | A valid notice on a server without Redis: the person stays signed in | None | Follow 11.8 |
| `Back-channel logout: revoked sessions for user {user.id} (email={user.email}, provider={matched_provider}, sessions_deleted={len(sessions)})` | Log (info) | `backend/open_webui/utils/oauth.py:2436-2442` | Each person signed out by a notice (personal data) | None | Confirms a provider-initiated sign-out |
| `Back-channel logout: completed for {len(users_to_logout)} user(s), {revoked_count} revocation(s) set` | Log (info) | `backend/open_webui/utils/oauth.py:2444-2446` | End of each processed notice; zero revocations means no Redis | None | As above |
| `⚠️  OAuth providers configured ({provider_list}) but OPENID_PROVIDER_URL not set - logout will not work!` | Log (warning, at start-up) | `backend/open_webui/config.py:2761-2774` | Google, Microsoft, GitHub or Feishu configured without `OPENID_PROVIDER_URL` or `OPENID_END_SESSION_ENDPOINT` (may overstate the problem, section 5.7) | None | Follow 11.7 |
| `Set OPENID_PROVIDER_URL to your OAuth provider's OpenID Connect discovery endpoint, or set OPENID_END_SESSION_ENDPOINT to a custom logout URL to fix logout functionality.` | Log (warning, at start-up) | `backend/open_webui/config.py:2775-2778` | Follows the line above | None | As above |
| `OAUTH_AUTHORIZE_PARAMS must be a JSON object, ignoring` | Log (warning, at start-up) | `backend/open_webui/config.py:2629-2631` | The variable holds JSON that is not an object | None | Escalate: configuration |
| `OAUTH_AUTHORIZE_PARAMS is not valid JSON, ignoring` | Log (warning, at start-up) | `backend/open_webui/config.py:2632-2633` | The variable is not JSON | None | As above |
| `GOOGLE_OAUTH_AUTHORIZE_PARAMS must be a JSON object, ignoring` | Log (warning, at start-up) | `backend/open_webui/config.py:2509-2511` | As above, for Google | None | As above |
| `GOOGLE_OAUTH_AUTHORIZE_PARAMS is not valid JSON, ignoring` | Log (warning, at start-up) | `backend/open_webui/config.py:2512-2513` | As above, for Google | None | As above |
| `Code challenge methods other than "S256" not supported. Given: "{OAUTH_CODE_CHALLENGE_METHOD}"` | Start-up stop | `backend/open_webui/config.py:2643-2648` | `OAUTH_CODE_CHALLENGE_METHOD` set to something other than `S256` while Google, Microsoft, GitHub or OIDC is configured; the server does not start. The code builds this text from a template whose first gap it fills with `S256`, so the source does not contain it word for word | None | Escalate: deployment |
| `SCIM is enabled but SCIM_AUTH_PROVIDER is not set. Set SCIM_AUTH_PROVIDER to the OAuth provider name (e.g. 'microsoft', 'oidc') to enable externalId storage.` | Log (warning, at start-up) | `backend/open_webui/env.py:911-916` | SCIM is on without `SCIM_AUTH_PROVIDER` | None | Section 5.11 |

## 11. Common Tier-1 Issues and Troubleshooting

Ground rules for every item below: tier 1 is read-only and never changes data, settings, roles,
groups or access. Never ask for, accept or repeat a password, session token, client secret, SCIM
token or provider token; if someone pastes one into a ticket, tell them to have it replaced and
treat it as a possible security incident (security.utoronto.ca). If a person reports seeing
someone else's account or data, stop and refer it as a possible privacy incident
(privacy.utoronto.ca, security.utoronto.ca). Email addresses and subject identifiers in
escalations are personal data: send them only through the approved ticket channel (**TO BE
CONFIRMED**). Which identity provider and which of these features production uses, the platform
maintainer's contact and the identity provider team's contact are **TO BE CONFIRMED** (section 14).

### 11.1 "The SSO button says my email or password is wrong"

**Symptom.** After choosing a **Continue with …** button, `/auth` shows the red pop-up
`The email or password provided is incorrect. Please check for typos and try logging in again.`
although the person typed no password.

**Likely causes, in order.**
1. The round trip was interrupted: the person cancelled or was refused at the provider, pressed
   Back or clicked twice so the one-time code was reused, or the round-trip cookie was lost because
   the sign-in started on a different address, in another browser or in a private window
   (`backend/open_webui/utils/oauth.py:1883-1920`; `backend/open_webui/main.py:2649-2674`).
2. The email domain is not in **Allowed Domains** (an exact, letter-case-sensitive match)
   (`backend/open_webui/utils/oauth.py:2002-2008`).
3. The provider sent no email or subject claim for this person, or the claim names in MedIT GPT do
   not match what the provider sends (`backend/open_webui/utils/oauth.py:1945-1999`).
4. The client secret expired or was changed at the provider, or MedIT GPT cannot reach the
   provider. This affects everyone at once (`backend/open_webui/utils/oauth.py:1912-1920`).

**Diagnostic steps.**
1. Record the button used, the exact time and time zone, whether it ever worked, and whether
   colleagues are affected.
2. Ask the person to try once more: one tab, starting at the usual MedIT GPT address, without the
   Back button.
3. If everyone fails, treat it as a configuration problem or provider outage and escalate at once.
4. If only one person fails, the cause is usually their email domain or the claims sent for them;
   the server log line for that moment names it (section 10.3).

**Resolution.** Guidance only: a clean retry. Tier 1 cannot change **Allowed Domains**, claims or
provider credentials.

**Escalation.** Send the provider button, time and time zone, how many people are affected,
whether a clean retry failed, and the person's email (through the ticket channel). Ask the
maintainer to read, for that time, the log line
`OAuth callback error during authorize_access_token for provider {provider}: {detailed_error}`
and any line beginning `OAuth callback failed,` (section 10.3).

### 11.2 "Single sign-on says I don't have permission"

**Symptom.** Straight after returning from the provider, `/auth` shows
`You do not have permission to access this resource. Please contact your administrator for assistance.`

**Likely causes, in order.**
1. The person has no account yet and **OAuth Signup** is off (its code default), so SSO cannot
   create one (`backend/open_webui/utils/oauth.py:2093-2095`, `:2148-2152`).
2. An account with the same email exists but is not linked to this provider (it was created by
   password, LDAP, SCIM, a trusted header or another provider) and **Merge Accounts by Email** is
   off (section 5.3).
3. **Role Mapping** is on and the person's roles claim holds none of the **Allowed Roles** or
   **Admin Roles** values, including when **Allowed Roles** was emptied (section 7.2)
   (`backend/open_webui/utils/oauth.py:1586-1608`).

**Diagnostic steps.**
1. Ask whether the person has used MedIT GPT before and how they signed in then.
2. Ask an admin to look the email up in the admin user list (read-only): does an account exist,
   and which providers does its **OAuth ID** list?
3. Ask the admin which of **OAuth Signup**, **Merge Accounts by Email** and **Role Mapping** are on
   (Authentication tab; read-only while persistence is off).
4. With role mapping on, the log line beginning
   `OAuth role management enabled but user roles do not match` names the roles received
   (section 10.3).

**Resolution.** Guidance only. Tier 1 cannot create or link accounts or change these settings. If
the person should have access, it is an access request through the organization's process
(**TO BE CONFIRMED**).

**Escalation.** Send the email (through the ticket channel), the provider, the time, whether the
admin list shows an account and which providers its **OAuth ID** lists, and the state of the three
switches.

### 11.3 "Single sign-on says my email is already registered"

**Symptom.** After SSO the pop-up reads
`Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.`

**Likely causes, in order.**
1. The person already has an account created another way (email and password, LDAP, SCIM, a
   trusted header or a different SSO provider); **OAuth Signup** is on and **Merge Accounts by
   Email** is off (`backend/open_webui/utils/oauth.py:2095-2099`).
2. The provider's subject identifier changed (new tenant, provider or **Sub Claim**), so the old
   link no longer matches (section 5.3).

**Diagnostic steps.** Ask how the person signed in before. Ask an admin which providers the
account's **OAuth ID** lists, and the maintainer whether the provider, tenant or **Sub Claim**
changed recently.

**Resolution.** If the earlier sign-in method is still offered, the person uses it. Linking the
accounts is an admin and policy decision (merging trusts the provider's email; section 5.3).

**Escalation.** Send the email (through the ticket channel), the provider used, the providers in
the account's **OAuth ID**, and when sign-in last worked.

### 11.4 "There's no single sign-on button"

**Symptom.** `/auth` shows only the email or LDAP form, or a button the person used before is
missing.

**Likely causes, in order.**
1. **OAuth / OIDC** is off, possibly in only some server processes after a change that bypassed
   the admin screen (section 7.1) (`backend/open_webui/main.py:2317-2326`).
2. The provider is not registered: a variable is missing (Microsoft also needs the tenant ID; OIDC
   needs the discovery address) or a redeploy changed the environment
   (`backend/open_webui/config.py:2653-2782`).
3. Trusted-header mode is on, which replaces the card with "Signing in to MedIT GPT"
   (`src/routes/auth/+page.svelte:235-248`).
4. The person is on a different MedIT GPT address, such as a test site (addresses are **TO BE
   CONFIRMED**).

**Diagnostic steps.** Confirm the address and get a screenshot. Ask whether colleagues see the
button. `/api/config` is readable without signing in: an empty `oauth.providers` list means no SSO
button can appear (`backend/open_webui/main.py:2317-2324`).

**Resolution.** Point the person to the official address (**TO BE CONFIRMED**); otherwise escalate.

**Escalation.** Send the address, screenshot, time, whether others are affected and what
`oauth.providers` lists.

### 11.5 "The SSO button shows 'Not Found' or 'Internal Server Error'"

**Symptom.** After the click, a bare page reads `{"detail":"Not Found"}` or
`Internal Server Error`.

**Likely causes, in order.**
1. **OAuth / OIDC** is off in the server process that answered, or the provider is no longer
   registered after a restart (`backend/open_webui/utils/oauth.py:1851-1859`).
2. The provider's discovery document could not be fetched (provider or network outage), which
   gives the 500 page (`backend/open_webui/utils/oauth.py:1870`).
3. The sign-in page was loaded before a configuration change; a reload shows the current buttons.

**Diagnostic steps.** Reload `/auth` and try again; note the time and whether the error comes and
goes (which suggests several server processes with different settings).

**Resolution.** Retry after a reload; otherwise escalate.

**Escalation.** Send the exact page text, the time, the provider and whether it is intermittent.

### 11.6 "After signing in at the identity provider I'm back on the sign-in page"

**Symptom.** The round trip completes but `/auth` shows the sign-in card again, without a pop-up.

**Likely causes, in order.** Read from the code, not exercised (section 14).
1. **WebUI URL** (`webui.url`) names a different address from the one the person used, so the
   session cookie set at the callback is not visible where the browser lands
   (`backend/open_webui/utils/oauth.py:2175-2198`).
2. The browser blocked or dropped the cookie (strict privacy settings, an extension, or cookie
   flags that require a secure address) (`backend/open_webui/env.py:769-778`).
3. A pop-up did appear and was missed.

**Diagnostic steps.** Ask which address the person typed, which browser, and whether a red message
flashed. Ask them to try in a normal window with extensions off. Check whether colleagues are
affected.

**Resolution.** Use the official address (**TO BE CONFIRMED**) and default browser settings;
otherwise escalate.

**Escalation.** Send the address typed, browser and version, private window or not, the time and
whether others are affected.

### 11.7 "I signed out but I'm still signed in to the identity provider"

**Symptom.** After **Sign Out**, choosing the SSO button signs the person straight back in without
asking for credentials, or other services that use the same provider stay signed in.

**Likely causes, in order.**
1. Expected behaviour: **Sign Out** ends the MedIT GPT session; the provider's own session ends
   only if MedIT GPT sends the browser to the provider's sign-out page (section 5.7).
2. No provider sign-out address: `OPENID_END_SESSION_ENDPOINT` is not set and the provider's
   discovery document names no end-session endpoint
   (`backend/open_webui/routers/auths.py:997-1037`).
3. The browser's stored SSO session no longer existed (removed by the session limit, a failed
   refresh or back-channel logout, or unreadable after a key change), so no provider sign-out was
   attempted (`backend/open_webui/routers/auths.py:1049-1059`; section 5.8).
4. The discovery document could not be read: the server answered
   `Failed to sign out from the OpenID provider.` and nothing visible happened
   (`backend/open_webui/routers/auths.py:1038-1047`).
5. The provider's sign-out page did not send the person back; which return addresses the
   production provider accepts is **TO BE CONFIRMED**.

**Diagnostic steps.** Ask what happened after **Sign Out**: did a provider page appear, and did the
person land on `/auth`? Ask whether this is a shared computer. The maintainer can check for the
start-up warning beginning `⚠️  OAuth providers configured` (section 10.3).

**Resolution.** Advise closing every browser window and, where needed, signing out at the
identity provider's own site (the U of T page is **TO BE CONFIRMED**); on shared computers, use a
private window. Escalate if provider sign-out is expected to work.

**Escalation.** Send the provider, the time, what appeared after **Sign Out**, and the browser.

### 11.8 "I signed out of the identity provider but MedIT GPT is still open"

**Symptom.** After signing out at the provider, or being disabled there, the person's open
MedIT GPT tab keeps working.

**Likely causes, in order.**
1. Expected without back-channel logout: the MedIT GPT session is independent of the provider's
   and lasts `auth.jwt_expiry` (code default four weeks) (section 5.8).
2. Back-channel logout is off (`ENABLE_OAUTH_BACKCHANNEL_LOGOUT`, code default off) or the provider
   is not set up to send notices (**TO BE CONFIRMED**) (`backend/open_webui/main.py:2858-2865`).
3. Back-channel logout is on but Redis is not configured: stored sessions are deleted, but the
   MedIT GPT session stays valid until it expires, with the log line beginning
   `Back-channel logout: Redis not configured` (`backend/open_webui/utils/oauth.py:2418-2424`).
4. The notice named only a provider session, not a person, so nobody was signed out
   (`backend/open_webui/utils/oauth.py:2409-2416`).
5. The notice was rejected; the identity provider's logs show one of the texts in section 10.1.

**Diagnostic steps.** Ask the maintainer whether back-channel logout and Redis are configured, and
record the time of the provider sign-out. Whether disabling someone at the provider is meant to
remove access at once is a policy question (**TO BE CONFIRMED**).

**Resolution.** None at tier 1. If the person must lose access now, escalate urgently: an admin can
suspend the account by setting its role to `pending` (`users-groups-roles-and-permissions.md`),
although with role mapping on a later SSO sign-in can undo that (11.12). Suspected security
incidents go to security.utoronto.ca.

**Escalation.** Send the account email (through the ticket channel), the time of the provider
sign-out, and whether it is urgent.

### 11.9 "SCIM-created accounts can't sign in"

**Symptom.** Accounts provisioned by the identity provider appear in the admin user list, but the
person cannot get in: the SSO button gives
`Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.`
or the permission message; the email form and trusted headers give the password message, and LDAP
gives `LDAP authentication failed.` (`backend/open_webui/routers/auths.py:703-709`).

**Likely causes, in order.**
1. SCIM creates accounts with no sign-in record and no SSO link; the first SSO sign-in links the
   account only when **Merge Accounts by Email** is on (`backend/open_webui/routers/scim.py:622-629`;
   `backend/open_webui/utils/oauth.py:2010-2019`).
2. The email the provider sends at sign-in differs from the SCIM email (letter case does not
   matter; spelling or an alias does) (`backend/open_webui/models/users.py:438-452`).
3. The account was created with `active: false` and is `pending`, so the person sees Account
   Activation Pending after signing in (`backend/open_webui/routers/scim.py:627`).
4. Password, LDAP and trusted-header sign-in cannot work for these accounts at all, because each
   needs the missing sign-in record (`backend/open_webui/models/auths.py:157-161`, `:178-194`;
   `backend/open_webui/routers/auths.py:690-709`, `:761`).

**Diagnostic steps.** Ask an admin to confirm (read-only) that the account exists, its role, and
whether its **OAuth ID** is empty. Compare the email the person uses at the provider with the
account's email. Ask whether **Merge Accounts by Email** is on.

**Resolution.** Guidance only; escalate. Linking needs **Merge Accounts by Email** (a policy
decision with a security note, section 5.3).

**Escalation.** Send the email (through the ticket channel), which sign-in method gives which
message, the account's role and whether its **OAuth ID** is empty, and the merge setting.

### 11.10 "I keep getting removed from my group"

**Symptom.** An admin adds the person to a group (or they are in the **Default Group**), but after
their next sign-in they are no longer a member, and models, knowledge or tools shared with that
group disappear for them.

**Likely causes, in order.**
1. **Group Mapping** is on: every SSO sign-in replaces memberships with the groups named in the
   claim, removing hand-assigned groups and the **Default Group** unless they match **Blocked
   Groups** (`backend/open_webui/utils/oauth.py:1730-1747`).
2. The group's name in MedIT GPT does not exactly match the value in the claim (letter case,
   spaces); whether the production provider sends names or identifiers is **TO BE CONFIRMED**
   (`backend/open_webui/utils/oauth.py:1765-1772`).
3. A trusted groups header replaces memberships at each sign-in
   (`backend/open_webui/routers/auths.py:763-768`).
4. LDAP group mapping does the same for LDAP sign-ins (`authentication-and-sign-in.md`).
5. The identity provider's SCIM client replaced the group's member list
   (`backend/open_webui/routers/scim.py:1035-1041`, `:1108-1118`).

**Diagnostic steps.** Ask whether the removal follows each sign-in. Ask an admin whether **Group
Mapping** is on and what **Blocked Groups** holds. If event webhooks exist, `group.member_removed`
deliveries show the source (`oauth` or `scim`; trusted-header changes publish nothing) (section 9).
Compare the group's exact name with the provider's group names.

**Resolution.** Explain that the group comes from the identity provider: the membership has to
change there, or an admin may decide to list the group in **Blocked Groups** so mapping leaves it
alone. Tier 1 changes nothing.

**Escalation.** Send the person's email (through the ticket channel), the group's exact name, the
times of the removals and the event source if known.

### 11.11 "I was an admin and now I'm a regular user"

**Symptom.** An admin finds the admin features gone after signing in.

**Likely causes, in order.**
1. **Role Mapping** is on and the person's roles claim carries an allowed role but no admin role,
   so each sign-in sets `user`; there is no exception for the primary admin
   (`backend/open_webui/utils/oauth.py:1586-1599`, `:1629-1635`; section 3.3).
2. A trusted role header now says `user` (`backend/open_webui/routers/auths.py:770-786`).
3. Another admin changed the role (`users-groups-roles-and-permissions.md`).
4. Not SCIM: SCIM's `active` flag does not change an existing admin
   (`backend/open_webui/routers/scim.py:692-696`, `:786-788`).

**Diagnostic steps.** Record the time of the last sign-in. If event webhooks exist, the
`user.role_updated` delivery shows the source (`oauth`, `trusted_header`, `scim` or `api`).
Ask the maintainer whether **Role Mapping** is on and what **Admin Roles** holds; what roles the
provider assigns the person is a question for the identity provider team (**TO BE CONFIRMED**).

**Resolution.** Escalate. Restoring the role by hand does not last while the claim is unchanged,
because role mapping applies again at the next sign-in; the fix is the person's role at the
provider or the **Admin Roles** setting.

**Escalation.** Send the account email (through the ticket channel), the time, the event source if
known, and whether other admins are affected. If every admin was demoted, mark it urgent.

### 11.12 "An account we suspended is active again" (admins)

**Symptom.** An admin set someone to `pending` to suspend them, but the account is `user` again.

**Likely causes, in order.**
1. **Role Mapping** is on: the next SSO sign-in with an allowed role sets `user` again
   (`backend/open_webui/utils/oauth.py:1586-1593`).
2. A trusted role header says `user` at the next sign-in
   (`backend/open_webui/routers/auths.py:770-786`).
3. The identity provider's SCIM client sent `active: true`
   (`backend/open_webui/routers/scim.py:692-696`, `:783-788`).

**Diagnostic steps.** As 11.11: the `user.role_updated` source, and the role-mapping settings.

**Resolution.** Escalate. While one of these paths is active, a lasting suspension has to happen at
the identity provider (role removed, account disabled, or SCIM `active: false`). Deleting an
account is permanent (ground truth).

**Escalation.** Send the account email (through the ticket channel), when it was suspended and
when it became active, and the event source if known.

### 11.13 "It just says 'Signing in to MedIT GPT' and never finishes"

**Symptom.** In trusted-header mode the page shows `Signing in to {{WEBUI_NAME}}` with a spinner,
possibly with a red pop-up.

**Likely causes, in order.**
1. The proxy did not pass the email header: pop-up
   `Your provider has not provided a trusted header. Please contact your administrator for assistance.`
   (`backend/open_webui/routers/auths.py:733-735`).
2. `ENABLE_PASSWORD_AUTH=False` also blocks trusted-header sign-in: pop-up
   `The requested action has been restricted as a security measure.`
   (`backend/open_webui/routers/auths.py:724-728`).
3. The account has no sign-in record (for example SCIM-created): the password message
   (`backend/open_webui/routers/auths.py:829-833`).
4. The proxy has not signed the person in yet and redirects the page; the app reloads `/` so the
   proxy's sign-in can appear (`src/lib/apis/index.ts:1469-1516`;
   `src/routes/+layout.svelte:1238-1250`).

**Diagnostic steps.** Note any pop-up text. Ask the person to reload and to sign in to the proxy
again. Check whether others are affected.

**Resolution.** Reload and sign in again at the proxy; otherwise escalate.

**Escalation.** Send the pop-up text, the time, the address and whether others are affected.

### 11.14 "It says 'User mismatch. Please sign in again.'"

**Symptom.** In trusted-header mode the session ends with `Session expired. Please sign in again.`
and the page signs in again, possibly as a different person.

**Likely causes, in order.** The proxy now reports a different email from the session's account,
for example on a shared computer or after the person switched accounts at the provider
(`backend/open_webui/utils/auth.py:462-468`).

**Diagnostic steps.** Ask whether the computer is shared and whether the person switched accounts.

**Resolution.** Sign out, close the browser and, on shared computers, sign out at the proxy or
provider too. If the person now sees someone else's account or chats, stop and refer it as a
possible privacy incident (privacy.utoronto.ca, security.utoronto.ca).

**Escalation.** Send the time and whether another person's account was visible.

### 11.15 "My name or photo keeps changing back"

**Symptom.** A name or photo edited in **Settings → Account** reverts at the next SSO sign-in, or an
uploaded photo is replaced by the default picture.

**Likely causes, in order.**
1. **Update Name** or **Update Picture** is on, so each SSO sign-in copies the provider's values
   (`backend/open_webui/utils/oauth.py:2038-2047`, `:2064-2082`).
2. With **Update Picture** on, a provider without a usable picture yields the default `/user.png`,
   which replaces the uploaded photo (`backend/open_webui/utils/oauth.py:1812-1848`).
3. **Update Email** can likewise change the account's email (section 5.4).

**Diagnostic steps.** Ask which field changed and when. Ask an admin which **Update** switches are
on.

**Resolution.** The change has to be made at the identity provider's directory (process **TO BE
CONFIRMED**), or an admin may decide to switch the option off.

**Escalation.** Send the email (through the ticket channel), the field and the times.

### 11.16 "New single sign-on users only see 'Account Activation Pending'"

**Symptom.** People signing in by SSO for the first time see the pending overlay.

**Likely causes, in order.** New SSO accounts get `ui.default_user_role` (code default `pending`)
when role mapping is off or the roles claim is empty
(`backend/open_webui/utils/oauth.py:1552-1553`, `:1609-1612`, `:2122`).

**Diagnostic steps and resolution.** As `authentication-and-sign-in.md` (pending accounts): an admin
approves the account; whether SSO accounts should start as `user` is a configuration decision.

**Escalation.** As described there, adding that the account was created by SSO.

### 11.17 "The tool server says to reconnect"

**Symptom.** In the chat composer a tool shows as an amber chip with the hover text
`Click to connect`, sending is refused with
`Please connect all required integrations before sending a message`, and in a new chat the
browser may jump to the tool's sign-in page by itself.

**Likely causes, in order.**
1. The person has never connected: each person connects their own account at the tool's service
   (`backend/open_webui/routers/tools.py:134-171`).
2. The connection's token could not be refreshed (expired or withdrawn at the tool's service, or no
   refresh token), so the connection was deleted (`backend/open_webui/utils/oauth.py:1042-1080`).
3. Back-channel logout deleted all of the person's stored sessions, tool connections included
   (`backend/open_webui/utils/oauth.py:2427-2430`).
4. The person used **Disconnect OAuth**.
5. Stored connection data became unreadable after a key change (sections 7.5 and 8). Many people
   are affected at once, the log asks to reconnect the tool server, and connecting shows
   `{"detail":"Not Found"}` until the tool-server admin reconnects it
   (`backend/open_webui/utils/oauth.py:921-927`; `backend/open_webui/main.py:2780-2783`).
6. An admin changed or removed the tool server.

**Diagnostic steps.** Ask the person to click the chip, complete the sign-in at the tool's service
and return. Note any error page or pop-up text. Find out whether one person or many are affected,
and how often it recurs (a daily recurrence points to failing refreshes).

**Resolution.** Guidance: click the chip and sign in at the tool's service. For an error page or
pop-up, see 11.18. If many people are affected or the page says `{"detail":"Not Found"}`, escalate
to the tool-server admin.

**Escalation.** Send the tool name, the time, the exact text, how many people are affected and how
often it recurs.

### 11.18 "Connecting a tool shows an error page or 'OAuth callback failed'"

**Symptom.** While connecting a tool, the browser shows a bare page such as
`{"detail":"Failed to re-register OAuth client"}`, or the home page shows a pop-up beginning
`OAuth callback failed:`, `Token exchange failed:`, `Failed to obtain OAuth token` or
`Failed to store OAuth session server-side`.

**Likely causes, in order.** The tool's service rejected MedIT GPT's registration; the tool server
was removed or its registration is unreadable; the round trip took too long or started in another
tab; a different MedIT GPT account is signed in; the tool's service had an error (the full list is
in the tool-server table of section 10.1).

**Diagnostic steps.** Record the exact text (the home-page message can be cut at 200 characters).
Ask the person to retry once from the same tab, and confirm which account is signed in.

**Resolution.** One clean retry; otherwise escalate.

**Escalation.** Send the tool name, the exact text and the time to the tool-server admin
(`workspace-tools-tool-servers-mcp-and-terminals.md`).

### 11.19 "My changes to the OAuth settings didn't stick" (admins)

**Symptom.** The **OAuth / OIDC** section is greyed out under a yellow notice; or a change saved
but sign-in behaves as before; or a change disappeared after a restart.

**Likely causes, in order.**
1. `ENABLE_OAUTH_PERSISTENT_CONFIG` is off (code default): the section is read-only and every value
   comes from the environment (section 7.1).
2. A change made outside the admin screen while persistence was off applied to one server process
   only and was lost at the restart (`backend/open_webui/models/config.py:198-206`).
3. Persistence is on, but the field is one sign-in does not read (client ID and secret, provider
   name and URL, redirect URI, scopes) (section 7.3).
4. Persistence is on and the environment was changed: the stored values win (section 7.1).

**Diagnostic steps.** Check whether the yellow notice is shown, which field changed, and when.

**Resolution.** Environment changes and restarts belong to the platform maintainer.

**Escalation.** Send the field, the intended change (never a secret's value) and the time.

### 11.20 "Our program gets 'User not found. Please sign in via the web interface first.'"

**Symptom.** A program using token exchange receives that answer.

**Likely causes, in order.** No account carries the token's subject for that provider (and, with
**Merge Accounts by Email** off, an account with the same email is not linked); token exchange
never creates accounts (`backend/open_webui/routers/auths.py:1732-1752`). Other answers are listed
in section 10.1.

**Diagnostic steps.** Ask whether the person has signed in on the website with the same provider.
An admin can check the account's **OAuth ID**.

**Resolution.** The person signs in once through the website with that provider, then the program
retries.

**Escalation.** Send the program owner, the provider, the time and the exact answer (never the
token).

### 11.21 "It sends me straight to the identity provider"

**Symptom.** Opening MedIT GPT jumps to the identity provider without showing the sign-in page.

**Likely causes, in order.** **Auto Redirect** is on and SSO is the only way in (section 5.1).

**Diagnostic steps.** Ask what the person wants to do: switching accounts usually means signing out
at the provider first.

**Resolution.** Guidance: after **Sign Out**, or after a failed sign-in, the sign-in card is shown
instead of forwarding (`src/routes/auth/+page.svelte:176-195`).

**Escalation.** Only if the provider's page shows an error: send a screenshot and the time.

### 11.22 "I see '[ERROR: Error during OAuth process]'"

**Symptom.** That pop-up appears on `/auth` after SSO.

**Likely causes, in order.** An unexpected failure during the callback, such as a database error or
a failure while applying group mapping (`backend/open_webui/utils/oauth.py:2167-2173`).

**Diagnostic steps.** Record the time and the provider; check whether others are affected.

**Resolution.** One retry; otherwise escalate.

**Escalation.** Send the time and provider; the maintainer reads the log line
`Error during OAuth process: {e}` for that time.

## 12. Local Customisations

Compared with upstream Open WebUI v0.11.4 (`git diff main...uoft`, and `git diff` for the working
tree), the single sign-on, trusted-header, SCIM, back-channel logout, token-exchange and
tool-server OAuth logic is unchanged. No fork commit and no uncommitted change touches
`backend/open_webui/utils/oauth.py`, `backend/open_webui/models/oauth_sessions.py`,
`backend/open_webui/routers/scim.py`, `backend/open_webui/routers/auths.py`,
`backend/open_webui/main.py`, `backend/open_webui/config.py`,
`backend/open_webui/models/config.py`, `backend/open_webui/events.py`,
`backend/open_webui/constants.py`, `backend/open_webui/utils/auth.py`,
`backend/open_webui/models/groups.py`, `backend/open_webui/routers/configs.py`,
`backend/open_webui/routers/tools.py`, `backend/open_webui/routers/users.py`,
`backend/open_webui/utils/tools.py`, `backend/open_webui/utils/middleware.py`,
`backend/open_webui/socket/main.py`, `src/routes/auth/+page.svelte`,
`src/lib/components/admin/Settings/Authentication.svelte`, `src/lib/apis/auths/index.ts`,
`src/lib/apis/configs/index.ts`, `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte`,
`src/lib/components/admin/Users/UserList/EditUserModal.svelte` or `src/routes/(app)/+page.svelte`.

Fork changes that show in this area:

| Change | Where it shows here | Source |
|---|---|---|
| Default product name `MedIT GPT`, and the upstream habit of appending ` (Open WebUI)` to a custom name removed | "Signing in to MedIT GPT" in trusted-header mode, the sign-in card's title, and the sender name of event webhooks | `backend/open_webui/env.py:951`; `backend/open_webui/main.py:538`; `backend/open_webui/events.py:1038` |
| U of T logo files | The logo on `/auth` | `authentication-and-sign-in.md` (section 12) |

`WEBUI_NAME` is an environment variable, so the live product name is **TO BE CONFIRMED** (ground
truth). The fork's other changes in files this document cites do not concern this area: two
interface settings in `backend/open_webui/models/users.py:99-100`, the task list hidden by **Hide
Processing Details** in `src/lib/components/chat/MessageInput.svelte:1792`, and browser
notification titles in `src/routes/+layout.svelte`.

**Upstream branding that remains.** These strings carry licence comments and are unchanged by the
fork; the project's instructions are to leave them intact (`CLAUDE.md`):

- The admin descriptions `Map OAuth claims to Open WebUI roles.` and
  `Map OAuth claims to Open WebUI groups.`
  (`src/lib/components/admin/Settings/Authentication.svelte:735-747`, `:786-800`;
  `src/lib/i18n/locales/en-US/translation.json:2070`, `:2108`).
- Automatic registration with a tool server's sign-in service names the application `Open WebUI`,
  so a tool's consent page may show that name rather than MedIT GPT
  (`backend/open_webui/utils/oauth.py:517-525`). What each tool's service displays is outside
  MedIT GPT.
- The tool-server discovery error names Open WebUI (`backend/open_webui/utils/oauth.py:576-583`).

**Uncommitted working-tree changes with an indirect effect.**

- `src/lib/i18n/index.ts` changes how the browser's language is matched and adds English as a
  final fallback. It changes which translation of this area's texts a person sees, not what the
  code does (detail in `authentication-and-sign-in.md`, section 12).
- `src/lib/components/chat/Chat.svelte` gains five lines at 2847-2851 about resuming after a tool
  approval. They do not concern OAuth but shift later line numbers; the citations of that file
  here (for example `src/lib/components/chat/Chat.svelte:3130-3133`) are to the working tree.
- `src/lib/i18n/locales/en-US/translation.json` changes one unrelated description (Hide Processing
  Details).

## 13. Source File Index

"Full" means the file was read from start to end while completing this document; "parts" lists
what was read. Sections 1 to 6 were written in an earlier session; the files they cite were
re-opened at the cited ranges listed here.

| File | What it holds for this area | Read |
|---|---|---|
| `backend/open_webui/utils/oauth.py` | SSO sign-in (`OAuthManager`: login, callback, role and group mapping, pictures, provider-token refresh, back-channel logout) and tool-server OAuth (`OAuthClientManager`: registration, discovery, connect and callback, refresh); callback error texts; blocked-group matching | Full |
| `backend/open_webui/models/oauth_sessions.py` | The `oauth_session` table and its repository (create, read, update, delete; removal of unreadable rows) | Full |
| `backend/open_webui/routers/scim.py` | SCIM 2.0 endpoints for users and groups, discovery documents, SCIM authentication and error format | Full |
| `backend/open_webui/routers/auths.py` | Trusted-header branch of sign-in, sign-up handler, sign-out and provider sign-out, tool-server disconnect, OAuth admin settings endpoints, token exchange and its rate limiter | Parts: 86-104, 167-227, 710-900, 952-1093, 1364-1514, 1585-1771 |
| `backend/open_webui/main.py` | Session middleware, `/oauth/*` routes, tool-server re-registration, start-up loading of tool-server registrations, SCIM mount, `/api/config` OAuth fields, reset and seeding at start-up | Parts: 355-375, 595-665, 2250-2262, 2312-2335, 2640-2870; lines 523-529, 538 and 885-887 by search |
| `backend/open_webui/config.py` | OAuth settings and their defaults, provider registration, start-up warnings, `DEFAULT_CONFIG` `oauth.*` keys, persistence switches | Parts: 36-50, 380-395, 2440-2830, 3150-3240; lines 1661, 1670, 1720, 1722 and 3082-3097 by search |
| `backend/open_webui/env.py` | Cookie flags, trusted-header variables, sign-out redirect, OAuth environment-only settings, token exchange, back-channel logout, SCIM, product name | Parts: 745-920, 950-970; lines 368 and 381 by search |
| `backend/open_webui/models/config.py` | How each key is read, written and seeded; the `oauth.*` exception | Parts: 100-280 |
| `backend/open_webui/constants.py` | `ERROR_MESSAGES` texts used here, including the `[ERROR: …]` wrapper | Parts: 1-135 |
| `backend/open_webui/events.py` | Event definitions, webhook message format and sender name, event sinks, live-connection disconnect on role change and deletion | Parts: 80-200, 660-680, 990-1210 |
| `backend/open_webui/utils/auth.py` | Token revocation for back-channel logout; the trusted-header `User mismatch` check | Parts: 340-372, 455-470 |
| `backend/open_webui/models/users.py` | `oauth` and `scim` columns, email and subject lookups, SCIM-visible accounts, link and external-ID updates, deletion | Parts: 168-175, 436-500, 775-815, 849-865 |
| `backend/open_webui/models/auths.py` | Trusted-header credential check (and its log line), email update through the sign-in record, deletion of the sign-in record | Parts: 175-240 |
| `backend/open_webui/models/groups.py` | Default share setting; trusted-header group sync | Parts: 135-146, 516-575 |
| `backend/open_webui/socket/main.py` | Disconnecting a person's live connections; the session-pool clean-up loop (not related to SSO) | Parts: 205-240, 380-410, 955-1000 |
| `backend/open_webui/routers/configs.py` | Admin registration of a tool server's OAuth client | Parts: 165-215 |
| `backend/open_webui/routers/tools.py` | Whether each MCP tool server is connected for the person | Parts: 125-175 |
| `backend/open_webui/routers/users.py` | An admin-only endpoint for a person's stored SSO sessions (not described; section 14) | Parts: 820-850 |
| `backend/open_webui/routers/openai.py` | Model connections forwarding the SSO token (**OAuth**) or using the server's Entra ID credential | Parts: 192-210 |
| `backend/open_webui/routers/terminals.py` | Terminals forwarding the SSO token | Parts: 170-183 |
| `backend/open_webui/functions.py` | Functions receiving the SSO token, with the fallback for requests without a cookie | Parts: 243-268 |
| `backend/open_webui/utils/tools.py` | Tool servers forwarding the SSO token or the tool-server connection token | Parts: 150-175 |
| `backend/open_webui/utils/middleware.py` | The SSO token for chat requests, with the fallback to the most recent stored session | Parts: 3796-3832 |
| `backend/open_webui/tasks.py`, `backend/open_webui/utils/automations.py` | Background loops (none related to this area) | Searched: loop definitions only |
| `backend/open_webui/migrations/versions/38d63c18f30f_add_oauth_session_table.py` | Creation of the `oauth_session` table | Parts: 1-40 |
| `src/routes/auth/+page.svelte` | Sign-in page: SSO buttons, `?error=` pop-up, return from SSO, Auto Redirect, trusted-header spinner | Parts: 1-260, 440-639; 260-440 (the password and LDAP form) searched for text |
| `src/lib/components/admin/Settings/Authentication.svelte` | Admin **OAuth / OIDC** section, read-only notice, save behaviour | Parts: 1-135, 544-887 |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted OAuth settings keys | Parts: keys `settings.admin.authentication.*` used here (2026-2134), plain keys quoted |
| `src/lib/apis/auths/index.ts` | Sign-out and its return-address logic; tool-server disconnect helper | Parts: 380-440, 633-661 |
| `src/lib/apis/configs/index.ts` | Starting a tool-server connection | Parts: 560-585 |
| `src/lib/apis/index.ts` | `/api/config` loading and the forward-auth proxy probe | Parts: 1469-1520 |
| `src/routes/(app)/+page.svelte` | Home-page `?error=` pop-up | Full |
| `src/routes/(app)/+layout.svelte` | Sending signed-out people to `/auth?redirect=…` | Parts: 195-218 |
| `src/routes/+layout.svelte` | Reconnect pop-ups; ending an expired session; proxy redirect handling | Parts: 928-952, 1236-1252; lines 162 and 192-194 by search |
| `src/lib/components/chat/Chat.svelte` | Pending tool connections, automatic forwarding, send block | Parts: 945-980, 1030-1060, 3126-3136, 4070-4090 |
| `src/lib/components/chat/MessageInput.svelte` | Amber **Click to connect** chips | Parts: 2540-2562 |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Connecting an unconnected tool; **Disconnect OAuth** | Parts: 240-262, 588-622 |
| `src/lib/components/admin/Users/UserList/EditUserModal.svelte` | **OAuth ID** in the admin user editor | Parts: 180-200 |
| `src/lib/components/AddConnectionModal.svelte` | **OAuth** and **Entra ID** authentication types for connections | Parts: 425-453 |
| `src/lib/components/AddToolServerModal.svelte` | **OAuth 2.1** and **OAuth 2.1 (Static)** tool-server types; the admin's registration messages | Parts: 100-160, 758-768 |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | **Sign Out** | Parts: 575-596 |
| `src/lib/i18n/index.ts` | Translation loading (uncommitted change, section 12) | Working-tree diff only |
| `.venv/lib/python3.12/site-packages/starlette/exceptions.py`, `.venv/lib/python3.12/site-packages/starlette/middleware/errors.py` (local environment, not repository code) | The framework's default `Not Found` and `Internal Server Error` texts | Parts: 7-12, 255-260 |
| `knowledgebase/tools/ground-truth.md`, `knowledgebase/tools/inventory.md`, `knowledgebase/reference/authentication-and-sign-in.md` | Verified facts, the list of background loops and settings, and the sibling document | Ground truth full; inventory full, with its long key lists searched; the sibling's headings and sections 7 to 14 |

## 14. Open Questions

Everything below could not be established from the repository. Items 1 to 12 are configuration or
organizational facts held outside the code; item 13 lists behaviours read from the code but not
exercised; items 14 to 16 refine the ground truth; items 17 to 19 record wording, unreachable
messages and a checker note; item 20 lists security-sensitive matters deliberately left
undescribed.

1. **Which identity provider production uses, and how.** The code has no UTORid, Shibboleth, SAML
   or `utoronto` reference; a UTORid sign-in could arrive only through the `microsoft` provider, the
   generic `oidc` provider or a trusted-header proxy (section 4). Which (if any), the provider behind
   it, and its tenant or discovery address are **TO BE CONFIRMED**.
2. **Registered providers and environment values**: which of the provider variables in section 7.4
   are set, `OAUTH_PROVIDER_NAME` (the button label), the redirect addresses registered at the
   provider, `OAUTH_CODE_CHALLENGE_METHOD`, `OAUTH_AUDIENCE`, `OAUTH_AUTHORIZE_PARAMS`, the separators,
   `ENABLE_OAUTH_EMAIL_FALLBACK`, `OAUTH_MAX_SESSIONS_PER_USER`, `ENABLE_OAUTH_ID_TOKEN_COOKIE`, the
   cookie flags, `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` and `OPENID_END_SESSION_ENDPOINT`.
3. **Live values of the `oauth.*` settings** (section 7.2) and whether
   `ENABLE_OAUTH_PERSISTENT_CONFIG`, `ENABLE_PERSISTENT_CONFIG` or `RESET_CONFIG_ON_START` are set;
   and the related settings `webui.url`, `ui.default_user_role`, `ui.default_group_id` and
   `auth.jwt_expiry` (section 7.10).
4. **Which optional features are on**: trusted headers (and which proxy), SCIM (and
   `SCIM_AUTH_PROVIDER`), back-channel logout (and whether the provider is set up to send notices to
   `/oauth/backchannel-logout`), token exchange (its limit and trusted client IDs), and any MCP tool
   servers using **OAuth 2.1** sign-in and who administers them.
5. **Whether Redis is configured and how many server processes run.** Redis decides whether
   back-channel logout ends sessions (section 5.9); the process count decides how far a change that
   bypasses the admin screen reaches while persistence is off (section 7.1).
6. **What the production provider sends**: the claim names for email, name, picture and subject;
   whether a roles claim and a groups claim exist; whether groups arrive as names or identifiers;
   letter case (sections 3.2, 5.6, 11.10).
7. **Which source governs roles and groups** (the identity provider through role and group mapping,
   SCIM, or admins by hand), and who decides changes to the provider, tenant or **Sub Claim** that
   would break existing account links (sections 5.3, 5.11).
8. **Account provisioning and access requests**: whether SSO creates accounts (**OAuth Signup**),
   whether SCIM pre-creates them, whether accounts are merged by email, whether new SSO accounts
   start as `pending`, who approves them, and the process people follow to ask for access.
9. **Sign-out at the U of T provider**: whether its discovery document names an end-session
   endpoint, which return addresses it accepts, what its sign-out and error pages say, and where
   people should sign out of it on shared computers (sections 5.2, 5.7, 11.7).
10. **Policy on removing access**: whether disabling someone at the identity provider must cut
    MedIT GPT access at once (which needs back-channel logout with Redis, or a shorter
    `auth.jwt_expiry`), and how suspensions should be done while role mapping or SCIM is active
    (sections 11.8, 11.12).
11. **Contacts and channels**: the platform maintainer, the identity provider team, the tool-server
    admins, the approved ticket channel for personal data, hours and service levels. None exists in
    the repository (ground truth).
12. **Environments and addresses**: the production and any test host names, and which address
    people should use (sections 2, 11.4, 11.6). Which event webhooks production has (section 9).
13. **Behaviours traced by reading, not by running the application** (the instructions forbid
    starting it): landing on the sign-in page again when **WebUI URL** differs from the address used,
    and a callback failure when cookie flags stop the round-trip cookie returning (section 5.2;
    11.6); the plain 500 page when the provider's discovery document cannot be fetched (section
    5.2); the start-up logout warning possibly overstating the problem for Google and Microsoft
    (section 5.7); the `SCIM_AUTH_PROVIDER` trap (section 5.11); a change made through the save
    endpoint while persistence is off reaching one process only (section 7.1); an emptied **Allowed
    Roles** field admitting only admin roles (section 7.2); tool-server connections showing
    `{"detail":"Not Found"}` after a key change until the tool server is reconnected (section 11.17).
    Each should be confirmed in a test environment.
14. **Ground-truth refinement, group sync.** The ground truth says group sync removes a person from
    every group not named in the claim, including groups assigned by hand. For SSO group mapping
    the code adds two exceptions: groups matching **Blocked Groups** are left alone, and an empty or
    missing claim changes nothing (`backend/open_webui/utils/oauth.py:1730-1772`). The trusted-header
    groups header likewise changes nothing when the header is empty
    (`backend/open_webui/routers/auths.py:763-768`). A refinement, not a contradiction; recorded for
    the maintainer.
15. **Ground-truth refinement, `oauth.*` persistence.** The ground truth says `oauth.*` keys follow
    the environment unless `ENABLE_OAUTH_PERSISTENT_CONFIG=True`. The code also shows that, even with
    persistence on, the provider registration fields (client ID and secret, discovery address,
    redirect address, scopes, button label) are taken from the environment at start-up, so editing
    them on the admin screen has no effect on sign-in; and that, with persistence off, the save
    endpoint still changes the value in the memory of the process that handles it
    (sections 7.1, 7.3). A refinement, not a contradiction.
16. **Ground-truth refinement, the password message.** Besides a blocked domain, a missing email or
    subject and a failed code exchange, the password message also appears when the provider returns
    no user details and when GitHub has no primary email (`backend/open_webui/utils/oauth.py:1941-1994`).
    A refinement, not a contradiction.
17. **Upstream wording that may not suit this deployment**: the **Blocked Groups** description says
    the groups are "blocked from signing in", which the code does not do; the **Provider URL**
    placeholder is a Google address; the **Allowed Roles** placeholder `*` suggests that an empty
    field allows every role; the descriptions naming Open WebUI are licence-protected
    (section 12). Whether to override the wording through `ui.i18n` (for strings that are not
    licence-protected) is **TO BE CONFIRMED**.
18. **Unreachable texts.** `Invalid token or unable to fetch user info` is replaced before it is
    sent (`backend/open_webui/routers/auths.py:1682-1696`); `SCIM is not enabled` cannot occur while
    the router is mounted only when SCIM is on (`backend/open_webui/routers/scim.py:259-267`;
    `backend/open_webui/main.py:885-887`); the home page's `An unknown error occurred.` fallback is
    never reached (`src/routes/(app)/+page.svelte:8-12`). Listed in section 10 for completeness.
19. **Checker note.** `knowledgebase/tools/verify_quotes.py` reports the start-up message about
    code challenge methods (the last-but-one row of section 10.3) as not found, because the code
    fills the first gap of its template with the constant `S256`
    (`backend/open_webui/config.py:2643-2648`). The quote is accurate; the flag is expected.
20. **Security-sensitive: refer to the platform maintainer and U of T Information Security
    (security.utoronto.ca).** The following were reviewed and deliberately not described: how
    stored SSO sessions, provider tokens and tool-server registrations are protected and how long
    they are kept (after sign-out, account deletion, or removal of a provider or tool server),
    including the admin-only interface for a person's stored SSO sessions; how back-channel logout
    notices and exchanged tokens are validated; whether **Merge Accounts by Email** is safe with the
    production provider, given the code's own warning that some providers do not verify email
    addresses (`backend/open_webui/main.py:2845-2846`); how the trusted-header proxy is protected
    against requests that bypass it; how the hidden login form interacts with single sign-on and
    **Auto Redirect** on the sign-in page; throttling on the SSO, SCIM and token-exchange paths; and
    how the SCIM bearer token is issued and rotated. None of these is needed for tier-1 diagnosis.
