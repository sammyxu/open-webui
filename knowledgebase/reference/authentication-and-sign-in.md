# Authentication, Sign-In and Accounts

## At a Glance

- **Sign-in methods in the code.** Email and password (the "login form"), LDAP, single sign-on
  through OAuth or OIDC providers, trusted headers set by a reverse proxy, and a no-login mode
  (`WEBUI_AUTH=False`). Which of these production uses is **TO BE CONFIRMED** (they are switched by
  settings and environment variables, not by code). Single sign-on and trusted headers are
  documented in depth in `sso-oauth-oidc-and-scim.md`; this document covers the sign-in page that
  offers them.
- **The sign-in page is `/auth`.** It builds itself from the public `/api/config` answer: whether
  the login form, LDAP, sign-up and single sign-on buttons appear depends on `ui.enable_login_form`,
  `ldap.enable`, `ui.enable_signup` and the configured OAuth providers
  (`backend/open_webui/main.py:2310-2335`; `src/routes/auth/+page.svelte:296`, `:425`, `:451`,
  `:589`).
- **The first account ever created becomes `admin`** and sign-up is then switched off
  (`backend/open_webui/routers/auths.py:874-879`). On a fresh installation the sign-in page shows a
  welcome screen and a **Create Admin Account** button (`src/routes/auth/+page.svelte:202`,
  `:411-415`).
- **Every later account gets the default user role**, `ui.default_user_role`, code default
  `pending` (`backend/open_webui/config.py:1720`, `:3096`). A `pending` user can sign in but sees
  only the **Account Activation Pending** overlay until an admin changes the role
  (`src/routes/(app)/+layout.svelte:445-446`).
- **Password rules.** With the default `bcrypt` algorithm a new password longer than 72 bytes is
  refused; an optional pattern check (off by default) can require more, and its message is whatever
  the operator set as `PASSWORD_VALIDATION_HINT` (`backend/open_webui/utils/auth.py:190-201`;
  `backend/open_webui/env.py:814-829`).
- **Sessions.** Signing in issues a session token (a JWT) that lasts `auth.jwt_expiry`, code
  default `4w` (four weeks) (`backend/open_webui/config.py:2466`). The browser keeps it in local
  storage under `token` and the server also sets a `token` cookie
  (`src/routes/auth/+page.svelte:52`; `backend/open_webui/routers/auths.py:196-207`). About one
  minute before expiry the page shows `Session expired. Please sign in again.` and returns the user
  to `/auth` (`src/routes/+layout.svelte:897`, `:948`, `:974-975`).
- **Sign-out revokes the token on the server only when Redis is configured**; without Redis the
  browser forgets the token but the token itself stays valid until it expires
  (`backend/open_webui/utils/auth.py:276-288`, `:315-323`). Whether production runs Redis is
  **TO BE CONFIRMED**.
- **Sign-in throttling.** 15 email-and-password attempts per email address per rolling window of
  about three minutes; the 16th answers `API rate limit exceeded`
  (`backend/open_webui/routers/auths.py:91`, `:818-822`). There is no account lockout.
- **API keys are off by default.** A user needs the global **API Keys** switch on
  (`auth.enable_api_keys`) and, unless they are an admin, the `features.api_keys` permission (code
  default off) (`backend/open_webui/routers/auths.py:1517-1525`; `backend/open_webui/config.py:1924`,
  `:2454`). Keys are managed in **Settings → Account → API keys**.
- **LDAP failures are generic.** Almost every LDAP problem reaches the user as
  `LDAP authentication failed.`; the real reason is only in the server log
  (`backend/open_webui/routers/auths.py:707-709`).
- **Local customisation.** The fork changes only the product name shown on these screens
  (`MedIT GPT`) and the logo image files; the authentication logic matches upstream Open WebUI
  v0.11.4 (section 12).

## 1. Purpose and Who Uses It

This area is everything between a person arriving at MedIT GPT and being allowed to use it, plus
the account-level credentials they manage afterwards:

- the sign-in page and the choice of sign-in method it offers;
- self-service sign-up, and how the very first administrator account is created;
- the **Account Activation Pending** overlay that `pending` accounts see;
- password rules and changing a password;
- the session token, how long it lasts, where the browser keeps it and what "session expired"
  looks like;
- signing out;
- personal API keys for programmatic access;
- LDAP directory sign-in;
- the sign-in rate limit; and
- the admin settings that govern all of the above (the **Authentication** tab in the admin part of
  the **Settings** window, also reachable at `/admin/settings/authentication`; section 2).

**Who uses it.**

| Who | What they do here | Evidence |
|---|---|---|
| Every person | Signs in, signs out, sees session-expiry notices | `src/routes/auth/+page.svelte`; `src/lib/components/layout/Sidebar/UserMenu.svelte:579-594`; `src/routes/+layout.svelte:931-950` |
| A new person (self-service) | Signs up when sign-up is open; usually lands in `pending` | `backend/open_webui/routers/auths.py:899-952`; `backend/open_webui/config.py:1720` |
| A `pending` person | Sees the Account Activation Pending overlay; can only check again or sign out | `src/lib/components/layout/Overlay/AccountPending.svelte` |
| A `user` or `admin` | Changes their password, manages their API key in **Settings → Account** | `src/lib/components/chat/Settings/Account.svelte`; `src/lib/components/chat/Settings/Account/UpdatePassword.svelte` |
| An `admin` | Sets the default role and group, opens or closes sign-up, hides the login form, switches API keys on, sets the session lifetime, writes the pending-overlay text, configures LDAP | `src/lib/components/admin/Settings/Authentication.svelte` |
| An operator (server environment) | Chooses the password algorithm and rules, cookie flags, no-login and trusted-header modes, password sign-in on or off | `backend/open_webui/env.py:751-864`; `backend/open_webui/config.py:1664-1670` |
| Tier 1 support | Reads symptoms and messages, checks settings with an admin, escalates | Sections 10 and 11 |

**Not covered here** (cross-referenced by file name):

- Single sign-on (OAuth and OIDC) end to end, trusted-header details, SCIM provisioning,
  identity-provider logout and back-channel logout: `sso-oauth-oidc-and-scim.md`.
- Roles, groups, permission keys, approving pending users, editing or deleting users, the admin
  **Add User** screen: `users-groups-roles-and-permissions.md`.
- Every other admin settings tab: `admin-settings-panels.md`.
- The rest of **Settings** (including the Profile and User Variables parts of the Account tab):
  `user-settings-and-personalisation.md`.

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; every path below is relative to the site root.

### 2.1 Screens

| Screen | How a person reaches it | Who sees it | Source |
|---|---|---|---|
| Sign-in page | `/auth`. Any app page opened without a valid session sends the browser to `/auth?redirect=<the page they wanted>` | Anyone not signed in | `src/routes/(app)/+layout.svelte:197-200`, `:213-216`, `:411-413` |
| First-run welcome screen | Shown on `/auth` only while the installation has no accounts at all | The person setting up a new installation | `backend/open_webui/main.py:2250-2252`; `src/routes/auth/+page.svelte:202`, `:216-222` |
| Account Activation Pending overlay | Covers every app page after a `pending` account signs in | `pending` accounts (and any role other than `user` or `admin`) | `src/routes/(app)/+layout.svelte:445-446` |
| **Settings → Account** | Click your name at the bottom of the sidebar, choose **Settings**, then **Account** (listed under **Profile**). Deep link: `/?settings=account` | `user` and `admin` | `src/lib/components/layout/Sidebar/UserMenu.svelte:576`; `src/lib/components/chat/SettingsModal.svelte:154`, `:253-258`; `src/routes/(app)/+layout.svelte:166-185` |
| **Settings → Admin → Authentication** | In the same **Settings** window, admins see an **Admin** list; **Authentication** sits in its **System** group. Deep link: `/admin/settings/authentication`, which forwards to `/?settings=admin:authentication` | `admin` only | `src/lib/components/chat/SettingsModal.svelte:159`, `:274-279`, `:748-776`; `src/routes/(app)/admin/settings/[tab]/+page.svelte` |
| **Sign Out** | User menu (your name at the bottom of the sidebar) → **Sign Out**; also the **Sign Out** link on the pending overlay; also automatic after a password change | Anyone signed in | `src/lib/components/layout/Sidebar/UserMenu.svelte:579-594`; `src/lib/components/layout/Overlay/AccountPending.svelte:70-79`; `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:25-36` |
| "Backend Required" page | `/error`; the app goes there when it cannot read `/api/config` at start-up | Anyone, when the server cannot be reached | `src/routes/+layout.svelte:1315-1317`; `src/routes/error/+page.svelte` |
| Admin user list (approving `pending` users) | User menu → **Admin Panel** (`/admin`, which forwards to `/admin/users`) | `admin` only | `src/lib/components/layout/Sidebar/UserMenu.svelte:534-555`; `src/routes/(app)/admin/+page.svelte`; details in `users-groups-roles-and-permissions.md` |

**Query parameters the sign-in page understands** (`src/routes/auth/+page.svelte:156-174`):

- `redirect` — where to go after a successful sign-in; it is also remembered in the browser's local
  storage as `redirectPath` so single sign-on round trips can return there
  (`src/routes/auth/+page.svelte:64-69`, `:163-165`).
- `error` — any text here is shown as a red pop-up when the page opens. Single sign-on failures use
  it (`src/routes/auth/+page.svelte:168-171`; see `sso-oauth-oidc-and-scim.md`).
- `state=logout` — added after signing out; it stops the page from immediately forwarding a
  signed-out person back to a single sign-on provider (`src/routes/auth/+page.svelte:158`, `:180`;
  `src/lib/apis/auths/index.ts:410-438`).

### 2.2 Server Endpoints

Useful when reading server logs or a browser's developer tools. All of these are mounted under
`/api/v1/auths` (`backend/open_webui/main.py:856`) except `/api/config`.

| Method and path | Purpose | Who may call it | Source |
|---|---|---|---|
| `GET /api/config` | Product name, version and the switches the sign-in page needs; more fields once signed in | Anyone (the sign-in page reads it before sign-in) | `backend/open_webui/main.py:2224-2472` |
| `POST /api/v1/auths/signin` | Email-and-password sign-in (also trusted-header and no-login sign-in) | Anyone | `backend/open_webui/routers/auths.py:717-833` |
| `POST /api/v1/auths/signup` | Self-service sign-up, including the first admin | Anyone, subject to the sign-up switches | `backend/open_webui/routers/auths.py:899-952` |
| `POST /api/v1/auths/ldap` | LDAP sign-in | Anyone, when LDAP is on | `backend/open_webui/routers/auths.py:475-709` |
| `POST /api/v1/auths/signout` | Sign out; clears cookies; may return a redirect address | Anyone | `backend/open_webui/routers/auths.py:955-1059` |
| `GET /api/v1/auths/` | Session check: who am I, my role, permissions and token expiry | Any signed-in account, including `pending` | `backend/open_webui/routers/auths.py:249-311` |
| `POST /api/v1/auths/update/password` | Change own password | Any signed-in account | `backend/open_webui/routers/auths.py:386-423` |
| `POST /api/v1/auths/update/profile` | Save name, photo, bio, gender, birth date | `user` or `admin` | `backend/open_webui/routers/auths.py:319-344` |
| `POST /api/v1/auths/update/timezone` | Record the browser's time zone | Any signed-in account | `backend/open_webui/routers/auths.py:356-378` |
| `GET`, `POST`, `DELETE /api/v1/auths/api_key` | Read, create (replace) or delete own API key | Signed-in, with the API-key switch and permission | `backend/open_webui/routers/auths.py:1517-1581` |
| `GET /api/v1/auths/admin/details` | Admin name and email for the pending overlay | Any signed-in account | `backend/open_webui/routers/auths.py:1171-1196` |
| `GET`, `POST /api/v1/auths/admin/config` | The User Access and Pending Accounts settings (and other general switches) | `admin` | `backend/open_webui/routers/auths.py:1204-1296` |
| `GET`, `POST /api/v1/auths/admin/config/ldap` and `/admin/config/ldap/server` | LDAP on or off; LDAP server settings | `admin` | `backend/open_webui/routers/auths.py:1299-1361` |
| `GET`, `POST /api/v1/auths/admin/config/oauth` | OAuth and OIDC settings | `admin` | `backend/open_webui/routers/auths.py:1506-1514`; see `sso-oauth-oidc-and-scim.md` |
| `POST /api/v1/auths/add` | Admin creates an account | `admin` | `backend/open_webui/routers/auths.py:1101-1163`; see `users-groups-roles-and-permissions.md` |
| `DELETE /api/v1/auths/oauth/sessions/{provider}` | Disconnect a tool-server OAuth session | `user` or `admin` | `backend/open_webui/routers/auths.py:1067-1093`; see `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `POST /api/v1/auths/oauth/{provider}/token/exchange` | Exchange an identity-provider token for a MedIT GPT session; off unless `ENABLE_OAUTH_TOKEN_EXCHANGE=True` | External clients | `backend/open_webui/routers/auths.py:1624-1771`; see `sso-oauth-oidc-and-scim.md` |

## 3. Roles and Permissions

### 3.1 The Three Roles in This Area

There are exactly three roles: `admin`, `user` and `pending` (`backend/open_webui/routers/auths.py:772`,
`:1283`). The front end treats any role other than `user` or `admin` like `pending`
(`src/routes/(app)/+layout.svelte:218-220`, `:445-446`). Role management itself (approving,
demoting, the primary admin) is in `users-groups-roles-and-permissions.md`.

| Action | `pending` | `user` | `admin` | Source |
|---|---|---|---|---|
| Sign in by any enabled method | Yes | Yes | Yes | `backend/open_webui/routers/auths.py:830-831` (no role check at sign-in) |
| Use the application (chats, models, settings) | No: the Account Activation Pending overlay replaces the app | Yes | Yes | `src/routes/(app)/+layout.svelte:445-462`; `backend/open_webui/utils/auth.py:567-576` |
| See the admin's name and email on the overlay | Yes, when **Admin Details** is on | Not applicable | Not applicable | `backend/open_webui/routers/auths.py:1171-1196`; `src/lib/components/layout/Overlay/AccountPending.svelte:54-58` |
| Sign out | Yes | Yes | Yes | `backend/open_webui/routers/auths.py:955-1059` |
| Change own password in **Settings → Account** | No screen (the overlay hides Settings) | Yes, when the Password section is shown | Yes, when shown | `src/lib/components/chat/Settings/Account.svelte:381-385`; the endpoint accepts any signed-in account, `backend/open_webui/routers/auths.py:386-392` |
| Save own profile (name, photo) | No | Yes | Yes | `backend/open_webui/routers/auths.py:319-325` (`get_verified_user`) |
| Create, view, replace or delete own API key | No screen | Only with the global **API Keys** switch on **and** the `features.api_keys` permission | With the global switch on (the permission is not needed) | `backend/open_webui/routers/auths.py:1517-1525`; `src/lib/utils/settings-access.ts:13-15` |
| See and copy own session token (**JWT Token**) in **Settings → Account** | No | No | Yes, inside the API keys section, so only when API keys are switched on | `src/lib/components/chat/Settings/Account.svelte:387`, `:402-456` |
| Change the **Authentication** settings | No | No | Yes | `backend/open_webui/routers/auths.py:1204-1205`, `:1269-1270` (`get_admin_user`) |
| Create an account for someone else (**Add User**) | No | No | Yes | `backend/open_webui/routers/auths.py:1101-1107` |

### 3.2 Which Role a New Account Gets

| How the account is created | Role given | Source |
|---|---|---|
| Self-service sign-up on `/auth` | `ui.default_user_role` (code default `pending`); the very first account becomes `admin` | `backend/open_webui/routers/auths.py:863-878`; `backend/open_webui/config.py:1720`, `:3096` |
| First LDAP sign-in | `ui.default_user_role`; the very first account becomes `admin` | `backend/open_webui/routers/auths.py:652-667` |
| Admin **Add User** | The role chosen in the form; the API's own default is `pending` | `backend/open_webui/routers/auths.py:1122-1129`; `backend/open_webui/models/auths.py:94-95` |
| Environment bootstrap (`WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` when no accounts exist) | `admin` | `backend/open_webui/main.py:376-380`; `backend/open_webui/utils/auth.py:634-665` |
| Trusted-header sign-in of an unknown email | `ui.default_user_role` (first account `admin`); a role header, when configured, can then set it | `backend/open_webui/routers/auths.py:747-786`; see `sso-oauth-oidc-and-scim.md` |
| Single sign-on, SCIM | See `sso-oauth-oidc-and-scim.md` | `backend/open_webui/utils/oauth.py:2117-2125` |

The **Default User Role** setting offers `pending`, `user` and `admin`
(`src/lib/components/admin/Settings/Authentication.svelte:143-155`); the server ignores any other
value sent to it (`backend/open_webui/routers/auths.py:1283-1284`). The live value is data,
**TO BE CONFIRMED**.

### 3.3 The API Key Permission

- The permission key is `features.api_keys` in the `user.permissions` setting; its code default
  comes from `USER_PERMISSIONS_FEATURES_API_KEYS`, default `False`
  (`backend/open_webui/config.py:1924`, `:2003`).
- Permissions add up across a user's groups; a group can grant `features.api_keys` even though the
  default does not (ground truth; detail in `users-groups-roles-and-permissions.md`).
- Admins skip the permission check but **not** the global switch: with `auth.enable_api_keys` off,
  nobody (admin included) can create or use a key (`backend/open_webui/routers/auths.py:1518-1525`;
  `backend/open_webui/utils/auth.py:526-536`).

### 3.4 How Refusals Look

- Endpoints for `user` and `admin` refuse other roles with HTTP 401 and the text
  `You do not have permission to access this resource. Please contact your administrator for assistance.`
  (`backend/open_webui/utils/auth.py:567-576`, `:625-631`; `backend/open_webui/constants.py:70-72`).
  The browser does not treat these as a lost session: it re-checks the session first and only
  signs the person out if that check also answers 401 (`src/routes/+layout.svelte:1080-1093`,
  `:952-963`).
- API-key refusals answer HTTP 403 (`backend/open_webui/routers/auths.py:1522-1525`;
  `backend/open_webui/utils/auth.py:526-536`, `:546-550`).

## 4. Key Concepts and Terminology

**Account.** One row in the `user` table (profile and role) paired, for accounts that can use a
password, with one row in the `auth` table (sign-in email, password credential and an active flag)
sharing the same id (`backend/open_webui/models/users.py:144-178`;
`backend/open_webui/models/auths.py:26-34`, `:104-142`). Email addresses are matched without regard
to letter case (`backend/open_webui/models/users.py:438-450`).

**Login form.** The email-and-password fields on `/auth`. The admin switch **Login Form**
(`ui.enable_login_form`) shows or hides it, and with it the sign-up link; it does not switch off
password sign-in on the server. The server-side switch is the environment variable
`ENABLE_PASSWORD_AUTH` (`backend/open_webui/config.py:1666`, `:1670`;
`backend/open_webui/routers/auths.py:724-728`). See section 7 for the security note.

**Sign-up.** Creating your own account on `/auth`. Governed by **New Sign Ups**
(`ui.enable_signup`) and the login form switch, and refused when either is off once any account
exists (`backend/open_webui/routers/auths.py:908-911`).

**Onboarding (first run).** The state of an installation with no accounts. `/api/config` then
carries `onboarding: true`, and the sign-in page shows a welcome screen and a **Create Admin
Account** button (`backend/open_webui/main.py:2250-2252`, `:2311`;
`src/routes/auth/+page.svelte:202`, `:411-415`).

**Pending.** The waiting role. A `pending` person can sign in but sees only the Account Activation
Pending overlay. "Suspending" someone means setting them back to `pending` (ground truth).

**Default user role and default group.** The role (`ui.default_user_role`) and optional group
(`ui.default_group_id`) given to every new account created by sign-up, LDAP, admin **Add User** or
trusted header (`backend/open_webui/routers/auths.py:868`, `:881-885`, `:669-673`, `:1132-1136`).
If the group cannot be added, the account is still created and the failure is only logged
(`backend/open_webui/utils/groups.py:20-24`).

**Session token (JWT).** A signed token issued at sign-in that identifies the account and, unless
expiry is switched off, carries an expiry time (`backend/open_webui/routers/auths.py:186-194`;
`backend/open_webui/utils/auth.py:232-243`). It is signed with the server's `WEBUI_SECRET_KEY`
(`backend/open_webui/utils/auth.py:51`, `:242`); if that key changes, every existing token stops
working (ground truth). The token is a credential: support staff should never ask a person to send
it.

**Token lifetime (JWT expiration).** The setting `auth.jwt_expiry`, code default `4w`, applied when
the token is issued (`backend/open_webui/config.py:2466`, `:3158`;
`backend/open_webui/routers/auths.py:186`). Changing it affects tokens issued afterwards only,
because each token carries its own expiry. Values `-1` and `0` mean no expiry
(`backend/open_webui/utils/misc.py:1012-1014`). No code in `backend/open_webui/routers/auths.py`
issues a replacement token while a person is active, so a session ends a fixed time after sign-in
whatever the person is doing.

**Session cookie.** At sign-in the server also sets an HttpOnly cookie named `token` holding the
same token, with the same expiry, `SameSite` taken from `WEBUI_AUTH_COOKIE_SAME_SITE` (default
`lax`) and `Secure` from `WEBUI_AUTH_COOKIE_SECURE` (default off)
(`backend/open_webui/routers/auths.py:196-207`; `backend/open_webui/env.py:769-778`). Each session
check sets it again (`backend/open_webui/routers/auths.py:279-289`).

**Revocation.** Making an unexpired token unusable. Sign-out revokes the one token used; a password
change revokes every token the account holds. Both need Redis; without it nothing is stored and
the tokens stay valid until they expire (`backend/open_webui/utils/auth.py:315-346`, `:349-371`).

**Redis.** An optional shared store (`REDIS_URL`). In this area it holds revocation markers and the
sign-in rate-limit counters (`backend/open_webui/utils/auth.py:276-312`;
`backend/open_webui/utils/rate_limit.py:79-93`). Whether production has it is **TO BE CONFIRMED**.

**Rate limit.** A cap of 15 email-and-password sign-in attempts per email address within a rolling
window counted in one-minute buckets (three minutes plus the current minute)
(`backend/open_webui/routers/auths.py:91`; `backend/open_webui/utils/rate_limit.py:27-30`, `:79-93`,
`:101-109`). Every attempt counts, successful or not, including attempts made while already
refused (`backend/open_webui/routers/auths.py:818-828`). Without Redis each server process keeps
its own count (`backend/open_webui/utils/rate_limit.py:55-61`).

**API key.** A personal secret beginning `sk-` that lets a program act as the person
(`backend/open_webui/utils/auth.py:378-380`, `:418-436`). Each account has at most one; creating a
new one removes the old one (`backend/open_webui/models/users.py:870-883`). No code in this area
gives keys an expiry date; a key keeps working until it is replaced or deleted, the global switch
is turned off, the person loses the permission, or the account is deleted
(`backend/open_webui/utils/auth.py:509-536`; `backend/open_webui/models/users.py:425-436`).
Changing the password does not affect the API key (`backend/open_webui/routers/auths.py:404-419`
touches only the password and the session tokens).

**API key endpoint restrictions.** An optional admin list of API paths that keys may call; any
other path answers 403 for key-based requests (`backend/open_webui/utils/auth.py:538-550`).

**LDAP.** Sign-in against a directory server (for example Active Directory) using a username and
password; the MedIT GPT account is matched or created by the directory's email attribute
(`backend/open_webui/routers/auths.py:475-709`).

**Trusted header.** A mode where a reverse proxy signs people in and passes their email in a
header named by `WEBUI_AUTH_TRUSTED_EMAIL_HEADER`; the sign-in page then signs in automatically
(`backend/open_webui/env.py:802-805`; `src/routes/auth/+page.svelte:199-200`). Detail in
`sso-oauth-oidc-and-scim.md`.

**No-login mode.** `WEBUI_AUTH=False` (code default `True`) turns off sign-in for a single-person
installation; it is refused once accounts exist, and sign-up is forced off in that mode
(`backend/open_webui/env.py:751`; `backend/open_webui/config.py:1664`;
`backend/open_webui/routers/auths.py:788-801`, `:915-917`). This document records only that the
setting exists.

**Password algorithm.** `PASSWORD_HASH_ALGORITHM`, code default `bcrypt`, `argon2` supported
(`backend/open_webui/env.py:815`; `backend/open_webui/utils/auth.py:178-187`). The production value
is **TO BE CONFIRMED**. It matters to users only through the 72-byte limit described in section 5.10.

**Primary admin, approval, groups.** See `users-groups-roles-and-permissions.md`.

## 5. Workflows (Step by Step)

### 5.1 How the Sign-In Page Decides What to Show

Before anyone signs in, the browser asks `GET /api/config` for the product name and a handful of
switches (`src/routes/+layout.svelte:1238-1240`, `:1267-1274`). The fields that drive `/auth` are:

| `/api/config` field | Comes from | Effect on `/auth` | Source |
|---|---|---|---|
| `name` | `WEBUI_NAME` (fork default `MedIT GPT`) | Used in every title on the page and the browser tab | `backend/open_webui/main.py:2313`; `src/routes/auth/+page.svelte:211-213` |
| `onboarding` | Present (`true`) only when no account exists and no valid token was sent | Welcome screen, then the **Create Admin Account** form | `backend/open_webui/main.py:2250-2252`, `:2311` |
| `features.auth` | `WEBUI_AUTH` (environment) | `false` means no-login mode: automatic sign-in | `backend/open_webui/main.py:2330` |
| `features.auth_trusted_header` | Whether `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` is set | `true` means automatic sign-in through the proxy | `backend/open_webui/main.py:2331` |
| `features.enable_login_form` | `ui.enable_login_form` | Shows the email and password fields | `backend/open_webui/main.py:2335` |
| `features.enable_ldap` | `ldap.enable` | Shows LDAP fields; the page opens in LDAP mode | `backend/open_webui/main.py:2333` |
| `features.enable_signup` | `ui.enable_signup` | Shows the "Don't have an account? Sign up" link | `backend/open_webui/main.py:2334` |
| `features.enable_signup_password_confirmation` | `ENABLE_SIGNUP_PASSWORD_CONFIRMATION` (environment, default off) | Adds a **Confirm Password** field to sign-up | `backend/open_webui/main.py:2332`; `backend/open_webui/env.py:754` |
| `oauth.providers` | OAuth providers registered from the environment; emptied when `oauth.enable` is off | One **Continue with …** button per provider | `backend/open_webui/main.py:2317-2324` |
| `oauth.auto_redirect` | `oauth.auto_redirect` | May forward straight to the single provider | `backend/open_webui/main.py:2325` |
| `metadata.login_footer`, `metadata.auth_logo_position` | Enterprise licence metadata only | Optional footer text and a centred logo | `backend/open_webui/main.py:2460-2469` |

What the page then does, in order (`src/routes/auth/+page.svelte:156-204`):

1. If the browser already holds a signed-in session and the address does not say `state=logout`,
   it goes straight to the `redirect` page or `/` (`:160-161`).
2. It remembers any `redirect` value (`:163-165`) and shows any `error` value as a red pop-up
   (`:168-171`).
3. It checks whether a single sign-on round trip has just left a session cookie and, if so, signs
   the person in (`:127-152`, `:173`; detail in `sso-oauth-oidc-and-scim.md`).
4. If **Auto Redirect** is on and the installation is single-sign-on only (exactly one provider,
   no login form, no LDAP, no trusted header, not first run, no session in the browser, and no
   `state=logout` or `error` in the address), it forwards the browser to that provider at once
   (`:180-195`).
5. With trusted headers or no-login mode it shows `Signing in to {{WEBUI_NAME}}` (displayed as
   "Signing in to MedIT GPT") with a spinner and
   signs in automatically (`:199-200`, `:235-248`).
6. Otherwise it shows the sign-in card, with the welcome screen first on a fresh installation
   (`:202`, `:216-222`).

What the sign-in card contains:

| Element | Shown when | Text (verbatim) | Source |
|---|---|---|---|
| Title | Always | `Get started with {{WEBUI_NAME}}` (first run), `Sign in to {{WEBUI_NAME}} with LDAP` (LDAP mode), `Sign in to {{WEBUI_NAME}}` (sign-in mode), `Sign up to {{WEBUI_NAME}}` (sign-up mode); `{{WEBUI_NAME}}` shows `MedIT GPT` | `src/routes/auth/+page.svelte:274-284` |
| First-run note | First run only | The symbol ⓘ and the product name, followed by `does not make any external connections, and your data stays securely on your locally hosted server.` | `src/routes/auth/+page.svelte:286-293` |
| **Name** field | Sign-up mode | Label `Name`, placeholder `Enter Your Full Name` | `src/routes/auth/+page.svelte:298-313` |
| **Username** field | LDAP mode | Label `Username`, placeholder `Enter Your Username` | `src/routes/auth/+page.svelte:315-330` |
| **Email** field | Sign-in and sign-up modes | Label `Email`, placeholder `Enter Your Email` | `src/routes/auth/+page.svelte:332-346` |
| **Password** field | Whenever fields are shown | Label `Password`, placeholder `Enter Your Password`; an eye button labelled for screen readers `Make password visible in the user interface` reveals what was typed | `src/routes/auth/+page.svelte:349-365`; `src/lib/components/common/SensitiveInput.svelte:55-63` |
| **Confirm Password** field | Sign-up mode with `ENABLE_SIGNUP_PASSWORD_CONFIRMATION` on | Label `Confirm Password`, placeholder `Confirm Your Password` | `src/routes/auth/+page.svelte:367-385` |
| Main button | Whenever fields are shown | `Authenticate` (LDAP), `Sign in`, `Create Admin Account` (first run) or `Create Account` | `src/routes/auth/+page.svelte:388-423` |
| Sign-up link | **New Sign Ups** on, not first run, not LDAP mode | `Don't have an account?` + `Sign up`, or `Already have an account?` + `Sign in` | `src/routes/auth/+page.svelte:425-445` |
| Single sign-on buttons | At least one provider and OAuth on | `Continue with {{provider}}` for Google, Microsoft, GitHub, the OIDC provider's display name (fallback `SSO`) and Feishu; a divider with `or` when fields are also shown | `src/routes/auth/+page.svelte:451-587` |
| LDAP and email toggle | LDAP and the login form both on | `Continue with Email` or `Continue with LDAP` | `src/routes/auth/+page.svelte:589-607` |
| Footer | Licence metadata only | Admin-supplied Markdown | `src/routes/auth/+page.svelte:609-615` |
| Logo | Always | The fork's logo file `/static/favicon.png`, top left (or centred with licence metadata) | `src/routes/auth/+page.svelte:252-265`, `:621-638` |

If the login form and LDAP are both off and no single sign-on provider is offered, the card shows
only its title: there are no fields, no button and no link (`src/routes/auth/+page.svelte:296`,
`:389`, `:451`).

### 5.2 Signing In with Email and Password

1. The person types their email and password and presses **Sign in**; the button shows a spinner
   and ignores further presses until the answer arrives (`src/routes/auth/+page.svelte:108-125`,
   `:405-423`).
2. The browser sends `POST /api/v1/auths/signin` (`src/lib/apis/auths/index.ts:312-342`).
3. The server refuses at once if password sign-in is switched off on the server
   (`ENABLE_PASSWORD_AUTH=False`): `The requested action has been restricted as a security measure.`
   (`backend/open_webui/routers/auths.py:724-728`).
4. It counts the attempt against the email address (lower-cased) and refuses with
   `API rate limit exceeded` once the address has more than 15 attempts in the window
   (`backend/open_webui/routers/auths.py:818-822`).
5. It looks the account up by email (any letter case) and checks the password; an unknown email,
   an account without a password credential, an inactive credential or a wrong password all give
   the same answer, `The email or password provided is incorrect. Please check for typos and try logging in again.`
   (`backend/open_webui/models/auths.py:144-164`; `backend/open_webui/routers/auths.py:824-833`).
6. On success it issues the session token, sets the `token` cookie and returns the account's id,
   email, name, role, permissions and token expiry (`backend/open_webui/routers/auths.py:167-230`).
   A role check does not happen here, so `pending` accounts sign in successfully.
7. The browser stores the token in local storage, shows `You're now logged in.`, joins the live
   connection, reloads the configuration, records the browser's time zone and goes to the
   `redirect` page or `/` (`src/routes/auth/+page.svelte:47-71`).
8. Any other refusal is shown as a red pop-up containing the server's text
   (`src/routes/auth/+page.svelte:73-80`).

If the browser cannot reach the server at all, or a proxy answers with something that is not
JSON, the sign-in helper ends without an error text and the page shows **nothing**: no pop-up, no
navigation (`src/lib/apis/auths/index.ts:326-341`; `src/routes/auth/+page.svelte:47-48`). The
reason appears only in the browser's developer console.

### 5.3 Signing Up

1. With **New Sign Ups** on, the person chooses **Sign up**, fills in **Name**, **Email**,
   **Password** (and **Confirm Password** if enabled) and presses **Create Account**
   (`src/routes/auth/+page.svelte:298-385`, `:405-445`).
2. If confirmation is enabled and the two passwords differ, the browser stops with
   `Passwords do not match.` (`src/routes/auth/+page.svelte:83-88`).
3. The browser draws an initials avatar and sends `POST /api/v1/auths/signup`
   (`src/routes/auth/+page.svelte:90-95`; `src/lib/utils/index.ts:454-484`).
4. Once any account exists, the server refuses unless both **New Sign Ups** and **Login Form** are
   on: `You do not have permission to access this resource. Please contact your administrator for assistance.`
   (`backend/open_webui/routers/auths.py:908-911`).
5. It checks the email shape (some text, an at sign, then a domain containing a dot; addresses
   ending `@localhost` are
   also accepted) and refuses an email already in use
   (`backend/open_webui/routers/auths.py:919-923`; `backend/open_webui/utils/misc.py:869-873`).
6. It applies the password rules in section 5.10 (`backend/open_webui/routers/auths.py:926-929`).
7. It creates the account with the default user role, adds it to the default group, publishes the
   sign-up event and signs the person in straight away (`backend/open_webui/routers/auths.py:841-896`,
   `:931-947`).
8. With the code default role `pending`, the next thing the person sees is the Account Activation
   Pending overlay (section 5.5).

### 5.4 Creating the First Admin Account (First Run)

1. On an installation with no accounts, `/auth` first shows a full-screen welcome: the product name,
   `Welcome to your AI home.`, a paragraph of upstream marketing text, a **Get started** button and a
   **Read the docs** link to the upstream documentation (`src/lib/components/OnBoarding.svelte:41-126`).
2. **Get started** opens the sign-up form titled `Get started with {{WEBUI_NAME}}`, which displays
   as "Get started with MedIT GPT" (or the LDAP form when
   LDAP is on) with the button **Create Admin Account** (`src/routes/auth/+page.svelte:216-222`,
   `:274-276`, `:411-415`).
3. The server does not require **New Sign Ups** for this first account. It refuses only when the
   login form is off and `ENABLE_INITIAL_ADMIN_SIGNUP` is not set
   (`backend/open_webui/routers/auths.py:912-914`; `backend/open_webui/env.py:753`).
4. The account is created with the default role and then, because it is the only account, promoted
   to `admin`; **New Sign Ups** is switched off at the same moment
   (`backend/open_webui/routers/auths.py:874-879`).
5. An operator can instead create the first admin from the environment (`WEBUI_ADMIN_EMAIL`,
   `WEBUI_ADMIN_PASSWORD`, optional `WEBUI_ADMIN_NAME`) at server start when no accounts exist; this
   also switches **New Sign Ups** off (`backend/open_webui/main.py:376-380`;
   `backend/open_webui/env.py:798-800`).
6. On LDAP, the first person to sign in through LDAP becomes `admin`, but that path does not switch
   **New Sign Ups** off (`backend/open_webui/routers/auths.py:663-667`).

Once any account exists, `/api/config` stops sending `onboarding` and the first-run screens no
longer appear (`backend/open_webui/main.py:2250-2252`, `:2311`).

### 5.5 Pending Approval and the Account Activation Pending Overlay

1. A `pending` account signs in by any method and the sign-in succeeds (section 5.2, step 6).
2. The app shell sees a role other than `user` or `admin`, stops loading the application (no
   sidebar, chats, models or settings) and shows the overlay full-screen
   (`src/routes/(app)/+layout.svelte:213-220`, `:440-447`).
3. The overlay reads its texts from `/api/config`, which sends the two overlay settings to
   `pending` accounts (`backend/open_webui/main.py:2450-2459`), and asks
   `GET /api/v1/auths/admin/details` for the admin contact
   (`src/lib/components/layout/Overlay/AccountPending.svelte:13-18`).

What the overlay shows (`src/lib/components/layout/Overlay/AccountPending.svelte:21-85`):

| Part | Default text (verbatim) | Replaced by | Source |
|---|---|---|---|
| Title | `Account Activation Pending`, a line break, then `Contact Admin for WebUI Access` | **Pending User Overlay Title** (`ui.pending_user_overlay_title`) when not blank, shown as plain text | `src/lib/components/layout/Overlay/AccountPending.svelte:31-36` |
| Message | `Your account status is currently pending activation.`, a new line, then `To access the WebUI, please reach out to the administrator. Admins can manage user statuses from the Admin Panel.` | **Pending User Overlay Content** (`ui.pending_user_overlay_content`) when not blank, shown as Markdown with line breaks kept (cleaned of unsafe HTML) | `src/lib/components/layout/Overlay/AccountPending.svelte:43-51` |
| Admin contact | `Admin: {name} ({email})` | Shown only when **Admin Details** (`auth.admin.show`) is on | `src/lib/components/layout/Overlay/AccountPending.svelte:54-58` |
| Button | `Check Again` | Reloads the app at `/` | `src/lib/components/layout/Overlay/AccountPending.svelte:61-68` |
| Link | `Sign Out` | Signs out (section 5.9) | `src/lib/components/layout/Overlay/AccountPending.svelte:70-79` |

Where the admin contact comes from (`backend/open_webui/routers/auths.py:1175-1194`):

- If **Admin Contact Email** (`auth.admin.email`) is set, that email is shown, with the name of the
  account that has that email; if no account has it, the name part is empty.
- If it is not set, the name and email of the **earliest-created account** are shown, whatever that
  account's current role (`backend/open_webui/models/users.py:715-720`).
- If **Admin Details** is off, the server refuses the request and the overlay simply omits the line
  (`backend/open_webui/routers/auths.py:1195-1196`; `src/lib/components/layout/Overlay/AccountPending.svelte:14-17`).

The admin's name and email are personal data shown to every `pending` account by design.

What happens next:

4. An admin changes the person's role to `user` (or `admin`) in the admin user list
   (`users-groups-roles-and-permissions.md`).
5. The person presses **Check Again** (or reloads). The role is read only when the page loads
   (`src/routes/+layout.svelte:1279-1288`); a role change disconnects the person's live connection,
   which reconnects on its own without re-reading the role (`backend/open_webui/events.py:1089-1100`;
   `src/routes/+layout.svelte:184-244`). Until the page reloads, the overlay stays.

The live overlay texts and **Admin Details** values are data, **TO BE CONFIRMED**.

### 5.6 Signing In with LDAP

1. With LDAP on, `/auth` opens in LDAP mode: title `Sign in to {{WEBUI_NAME}} with LDAP` (displayed
   as "Sign in to MedIT GPT with LDAP"), fields
   **Username** and **Password**, button **Authenticate**. If the login form is also on, a
   `Continue with Email` link switches to the email form and back (`src/routes/auth/+page.svelte:34`,
   `:277-278`, `:315-330`, `:390-403`, `:589-607`).
2. The browser sends `POST /api/v1/auths/ldap` with the username and password
   (`src/lib/apis/auths/index.ts:113-143`).
3. The server refuses straight away if LDAP is off (`LDAP authentication is not enabled`), if
   password sign-in is off on the server (`The requested action has been restricted as a security measure.`),
   or if the password is blank (`The email or password provided is incorrect. Please check for typos and try logging in again.`)
   (`backend/open_webui/routers/auths.py:482-498`).
4. It prepares the TLS settings; a problem there gives
   `Failed to configure TLS for LDAP connection.` (`backend/open_webui/routers/auths.py:515-524`).
5. It connects with the **Application DN** account (or anonymously when none is set) and searches
   under **Search Base** for an entry whose **Attribute for Username** equals the typed username
   (lower-cased), combined with any **Search Filters** (`backend/open_webui/routers/auths.py:526-565`).
6. It reads the entry's **Attribute for Mail** (the first value if there are several, lower-cased)
   and its `cn` (`backend/open_webui/routers/auths.py:567-588`).
7. It confirms the typed username is one of the entry's username values, then checks the typed
   password against the directory by signing in as that entry
   (`backend/open_webui/routers/auths.py:636-645`).
8. If no MedIT GPT account has that email, it creates one: name from `cn`, the default user role
   (the very first account becomes `admin`), the default group
   (`backend/open_webui/routers/auths.py:647-688`). **New Sign Ups** is not consulted on this path.
9. With **Group Mapping** on, it replaces the person's group memberships with the directory groups
   (creating missing groups when **Auto-Create Groups** is on); a failure here is only logged
   (`backend/open_webui/routers/auths.py:692-700`).
10. It issues the session exactly as for a password sign-in (`backend/open_webui/routers/auths.py:702`).

Every failure in steps 5 to 9 is caught and replaced by the single message
`LDAP authentication failed.` (`backend/open_webui/routers/auths.py:707-709`). The specific reason
is written to the server log as `LDAP authentication error: ` followed by the status and the
original text, for example the line "LDAP authentication error: 400: User not found in the LDAP
server" (the status-and-text format is how the web framework prints these errors). The specific reasons
are listed in section 10.

Accounts created by LDAP have no local password the person knows, so they cannot use the email
form or **Change Password** (`backend/open_webui/routers/auths.py:652-658`).

### 5.7 What Happens on Every Page Load (Session Bootstrap)

1. The app installs a watcher on its own requests: if a request to the server that carries a token
   answers 401 while a token is stored, it asks `GET /api/v1/auths/` once more; if that also
   answers 401, it ends the session as in section 5.8 (`src/routes/+layout.svelte:1079-1093`,
   `:918-929`, `:952-963`).
2. It reads `/api/config`. If a single sign-on proxy in front of the site redirects that request,
   the browser reloads `/` so the proxy's own login page can appear; any other failure sends the
   browser to `/error` (`src/routes/+layout.svelte:1238-1250`, `:1315-1317`;
   `src/lib/apis/index.ts:1469-1516`).
3. It opens the live connection (Socket.IO at `/ws/socket.io`), passing the stored token
   (`src/routes/+layout.svelte:166-175`, `:1276-1277`).
4. If a token is stored, it calls `GET /api/v1/auths/`. On success it keeps the account details
   (including role, permissions and `expires_at`), reloads the configuration and records the time
   zone. On failure it shows the server's refusal text as a red pop-up and deletes the stored token
   (`src/routes/+layout.svelte:1279-1312`).
5. It starts a timer that checks the token's expiry every 15 seconds (`src/routes/+layout.svelte:1219-1231`).
6. The app shell sends anyone without a session to `/auth?redirect=<page>` and shows the pending
   overlay to `pending` accounts (`src/routes/(app)/+layout.svelte:197-220`, `:411-413`, `:440-447`).

### 5.8 When a Session Expires

The browser ends a session in three ways:

- **Timer.** Every 15 seconds, and whenever the tab becomes visible again, it compares the token's
  expiry with the clock and ends the session 60 seconds early (`src/routes/+layout.svelte:897`,
  `:965-977`, `:1182-1183`, `:1231`).
- **A refused request.** Any request answering 401 triggers the re-check in section 5.7, step 1.
- **A fresh page load** with a token the server no longer accepts (section 5.7, step 4).

Ending the session means: forget the account, delete the stored token, clear the readable cookie,
ask the server to sign out, and show `Session expired. Please sign in again.`
(`src/routes/+layout.svelte:931-950`). The app shell then sends the person to
`/auth?redirect=<the page they were on>`, so they return there after signing in
(`src/routes/(app)/+layout.svelte:197-200`, `:411-413`).

On a fresh page load the code path produces **two** pop-ups: `Session expired. Please sign in again.`
from the watcher, and the server's own refusal text from the session check
(`src/routes/+layout.svelte:1080-1090`, `:1281-1284`). The second one tells support why:

| Server text in the second pop-up | What it means | Source |
|---|---|---|
| `401 Unauthorized` | The token has expired, or it can no longer be read (for example the server's secret key changed) | `backend/open_webui/utils/auth.py:246-251`, `:489-493`; `backend/open_webui/constants.py:69` |
| `Invalid token` | The token was revoked, which happens only with Redis: the password was changed (by the person or by an admin), the identity provider ended the session (`sso-oauth-oidc-and-scim.md`), or this very token was used to sign out | `backend/open_webui/utils/auth.py:276-312`, `:449-453`, `:349-371`; `backend/open_webui/routers/users.py:962-970` |
| `Your session has expired or the token is invalid. Please sign in again.` | The token is fine but its account no longer exists | `backend/open_webui/utils/auth.py:455-460`; `backend/open_webui/constants.py:59` |
| `User mismatch. Please sign in again.` | Trusted-header mode only: the proxy now reports a different person | `backend/open_webui/utils/auth.py:462-468` |

Every 401 answer from the session check also tells the browser to delete the `token` cookie and *Precision 2026-10-11 (to confirm in a test environment): the session check deletes the cookie on the response object injected into the dependency, which FastAPI discards when the dependency raises; the deletion may therefore not reach the browser (see `backend-architecture-and-request-lifecycle.md` section 14).*
the single sign-on cookies (`backend/open_webui/utils/auth.py:494-506`).

With **JWT Expiration** set to `-1` (or `0`) tokens carry no expiry, `expires_at` is empty and the
timer never fires (`backend/open_webui/routers/auths.py:186-189`; `src/routes/+layout.svelte:969-972`).

### 5.9 Signing Out

1. The person opens the user menu (their name at the bottom of the sidebar) and chooses
   **Sign Out** (`src/lib/components/layout/Sidebar/UserMenu.svelte:579-594`).
2. The browser sends `POST /api/v1/auths/signout` (`src/lib/apis/auths/index.ts:382-408`).
3. The server finds the token (header or cookie). With Redis configured it records that token as
   revoked and disconnects the account's live connections; without Redis nothing is stored. It
   publishes the `auth.logout` event (`backend/open_webui/routers/auths.py:958-983`;
   `backend/open_webui/utils/auth.py:315-346`).
4. It deletes the cookies `token`, `owui-session`, `oui-session` and `oauth_id_token`, and
   `oauth_session_id` for single sign-on sessions (`backend/open_webui/routers/auths.py:985-995`).
5. For a single sign-on session it may answer with the identity provider's logout address
   (`backend/open_webui/routers/auths.py:994-1047`; `sso-oauth-oidc-and-scim.md`). Otherwise, if
   `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` is set, it answers with that address
   (`backend/open_webui/routers/auths.py:1049-1057`).
6. The browser clears its session storage, deletes the stored token and goes to
   `/auth?state=logout`, or to the returned address with the sign-in page added as the place to
   come back to (`src/lib/apis/auths/index.ts:406`, `:410-438`;
   `src/lib/components/layout/Sidebar/UserMenu.svelte:583-586`).

Points to know:

- **This browser only.** Sign-out deals with the one token this browser holds; other browsers and
  devices keep their own tokens and stay signed in (`backend/open_webui/utils/auth.py:315-340`). To
  end every session, change the password (with Redis; section 5.11).
- **Without Redis** the token is not revoked on the server and stays valid until it expires
  (`backend/open_webui/utils/auth.py:285-286`, `:322-323`).
- **If the server's sign-out call fails** from the user menu (for example
  `Failed to sign out from the OpenID provider.`), the menu's code has no error handling, so the
  token stays in the browser and nothing visible happens
  (`src/lib/components/layout/Sidebar/UserMenu.svelte:582-587`;
  `backend/open_webui/routers/auths.py:1041-1047`). The pending overlay and the password-change
  screen ignore sign-out errors and continue to the sign-in page
  (`src/lib/components/layout/Overlay/AccountPending.svelte:73-78`;
  `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:29-35`).

### 5.10 Password Rules

The same check runs wherever a new password is set: self-service sign-up, **Change Password**, the
admin **Add User** screen and an admin setting someone's password in the user editor
(`backend/open_webui/routers/auths.py:926-929`, `:404-407`, `:1116-1119`;
`backend/open_webui/routers/users.py:962-966`). It does **not** run at sign-in, so an existing
password that breaks a newly introduced rule keeps working (`backend/open_webui/routers/auths.py:824-828`).

| Rule | When it applies | Message when broken (verbatim) | Source |
|---|---|---|---|
| At most 72 bytes | When `PASSWORD_HASH_ALGORITHM` is `bcrypt` (the code default) | `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | `backend/open_webui/utils/auth.py:53`, `:191-195`; `backend/open_webui/constants.py:48-50` |
| Must match a pattern | Only when `ENABLE_PASSWORD_VALIDATION=True` (code default `False`) | The operator's `PASSWORD_VALIDATION_HINT` text if set; otherwise `The password does not meet the required validation criteria.` | `backend/open_webui/utils/auth.py:197-199`; `backend/open_webui/env.py:814-829`; `backend/open_webui/constants.py:114` |

About the 72-byte rule:

- It counts bytes, not characters. Plain English letters, digits and common symbols take one byte
  each; accented letters such as é take two; many emoji take four. A long passphrase with accents
  can therefore be refused below 72 characters.
- Exactly 72 bytes is accepted; the check refuses only more than 72 (`backend/open_webui/utils/auth.py:192`),
  although the message says "less than 72".

About the optional pattern:

- The code default pattern requires at least eight characters including a lower-case letter, an
  upper-case letter, a digit and a symbol (a character that is not a letter, digit, underscore or
  space) (`backend/open_webui/env.py:816-819`).
- If the operator's pattern cannot be read, the server logs `Invalid PASSWORD_VALIDATION_REGEX_PATTERN: {e}`
  and falls back to the default pattern (`backend/open_webui/env.py:822-827`).
- Because the default hint is empty, people refused by the pattern see only the generic message
  and are not told the rule unless the operator wrote a hint.

The sign-up and **Change Password** screens show no rules in advance; people learn them only from
a refusal (`src/routes/auth/+page.svelte:349-385`;
`src/lib/components/chat/Settings/Account/UpdatePassword.svelte:73-131`). With the optional check
off (the code default), the 72-byte limit is the only rule. Production's values for
`PASSWORD_HASH_ALGORITHM`, `ENABLE_PASSWORD_VALIDATION`, the pattern and the hint are
**TO BE CONFIRMED**.

### 5.11 Changing Your Password

1. Open **Settings → Account**. The **Password** section appears only when both the login form and
   the password-change form are switched on (`src/lib/components/chat/Settings/Account.svelte:381-385`).
2. The row **Change Password** (description `Update the password used for email and password sign-in.`)
   has a **Show** / **Hide** toggle (`src/lib/components/chat/Settings/Account/UpdatePassword.svelte:57-71`;
   `src/lib/i18n/locales/en-US/translation.json:2749-2750`).
3. Fill in **Current Password** (placeholder `Enter your current password`), **New Password**
   (`Enter your new password`) and **Confirm Password** (`Confirm your new password`), then press
   **Update password** (`src/lib/components/chat/Settings/Account/UpdatePassword.svelte:73-131`; `src/lib/i18n/locales/en-US/translation.json:2751`, `:2753`, `:2760`, `:2767`).
4. If the two new entries differ, the browser stops with
   `The passwords you entered don't quite match. Please double-check and try again.` and clears both
   new-password fields (`src/lib/components/chat/Settings/Account/UpdatePassword.svelte:41-46`).
5. The browser sends `POST /api/v1/auths/update/password` (`src/lib/apis/auths/index.ts:527-556`).
6. The server refuses in trusted-header mode (`The requested action has been restricted as a security measure.`),
   refuses a wrong current password (`The password provided is incorrect. Please check for typos and try again.`),
   applies the password rules, saves the new password, revokes **every** session token the account
   holds (with Redis) and publishes `auth.password_changed`
   (`backend/open_webui/routers/auths.py:386-423`).
7. The browser shows `Password updated. Please sign in again.`, signs out and opens the sign-in
   page (`src/lib/components/chat/Settings/Account/UpdatePassword.svelte:25-36`).

Points to know:

- **Without Redis** other browsers and devices stay signed in; the server logs
  `Cannot revoke tokens for user {user_id}: Redis is not configured, existing sessions stay valid until expiry.`
  (`backend/open_webui/utils/auth.py:349-358`).
- **Single sign-on and LDAP accounts** were given a password nobody knows, so this form answers
  `The password provided is incorrect. Please check for typos and try again.` for them; their
  password is managed by the identity provider or directory (`backend/open_webui/utils/oauth.py:2117-2125`;
  `backend/open_webui/routers/auths.py:652-658`). The U of T process for those passwords is
  **TO BE CONFIRMED**.
- **No self-service reset.** No forgotten-password route exists in
  `backend/open_webui/routers/auths.py`, and the application sends no email (ground truth). An admin
  can set a new password in the admin user editor (`backend/open_webui/routers/users.py:962-970`;
  `users-groups-roles-and-permissions.md`), which also revokes that person's sessions when Redis is
  configured.
- The password-change form switch, `ui.enable_password_change_form`, is seeded from the environment
  variable `ENABLE_PASSWORD_CHANGE_FORM` (default on) and no admin screen writes it
  (`backend/open_webui/config.py:1668`, `:3085`; `backend/open_webui/main.py:2346`).

### 5.12 Managing Your API Key in Settings → Account

1. The **API keys** section appears only when the global **API Keys** switch is on and the person is
   an admin or holds `features.api_keys` (`src/lib/components/chat/Settings/Account.svelte:387`;
   `src/lib/utils/settings-access.ts:13-15`).
2. Its first row, **Secrets** (description `Show or hide sensitive account secrets.`), has a
   **Show** / **Hide** toggle (`src/lib/components/chat/Settings/Account.svelte:389-398`; `src/lib/i18n/locales/en-US/translation.json:2761-2762`).
3. After **Show**:
   - Admins see **JWT Token** (description `Copy the current session token for authenticated requests.`):
     their current session token, masked, with a copy button (screen-reader label `Copy Token`)
     (`src/lib/components/chat/Settings/Account.svelte:402-456`; `src/lib/i18n/locales/en-US/translation.json:2756-2757`).
   - Everyone with access sees **API Key** (description `Create, copy, or rotate your API key.`)
     (`src/lib/components/chat/Settings/Account.svelte:458-462`; `src/lib/i18n/locales/en-US/translation.json:2743-2744`):
     - with no key yet, a button **Create new secret key** (`src/lib/components/chat/Settings/Account.svelte:551-562`;
       `src/lib/i18n/locales/en-US/translation.json:2752`);
     - with a key, the key masked (an eye button reveals it), a copy button (screen-reader label
       `Copy API Key`) and a `More` menu holding **Create new key** and **Delete**
       (`src/lib/components/chat/Settings/Account.svelte:464-550`).
4. **Create** sends `POST /api/v1/auths/api_key`; on success the pop-up says `API Key created.` and the
   key appears. A new key **replaces** the previous one, which stops working immediately
   (`src/lib/components/chat/Settings/Account.svelte:181-188`; `backend/open_webui/routers/auths.py:1529-1550`;
   `backend/open_webui/models/users.py:870-883`).
5. **Delete** asks for confirmation: title `Delete API Key?`, text `This will revoke the current API key.`,
   button **Delete**. It then sends `DELETE /api/v1/auths/api_key` and shows `API Key deleted.`
   (`src/lib/components/chat/Settings/Account.svelte:190-200`, `:583-592`).
6. Each time the tab opens, the browser quietly fetches the current key; any error there, including
   "no key yet", is written only to the browser console (`src/lib/components/chat/Settings/Account.svelte:225-235`).

If the server refuses creation (for example the switch was turned off after the page loaded), the
create button's code has no error handling: no pop-up appears and the field does not change
(`src/lib/components/chat/Settings/Account.svelte:181-188`; `src/lib/apis/auths/index.ts:577-580`). `Failed to create API Key.`
appears only if the server reports success without returning a key.

### 5.13 Using an API Key

- A program sends the key either as a bearer token (`Authorization: Bearer sk-…`) or in the header
  named by `CUSTOM_API_KEY_HEADER` (default `x-api-key`) (`backend/open_webui/utils/asgi_middleware.py:126-132`;
  `backend/open_webui/env.py:812`).
- The server checks, in this order (`backend/open_webui/utils/auth.py:509-550`):
  1. the key belongs to an existing account, otherwise 401
     `Your session has expired or the token is invalid. Please sign in again.`;
  2. the global **API Keys** switch is on, otherwise 403 `Use of API key is not enabled in the environment.`;
  3. the account is an admin or holds `features.api_keys`, otherwise the same 403 text;
  4. if **API Key Endpoint Restrictions** is on, the path is one of **Allowed Endpoints** (or below
     one), otherwise 403
     `You do not have permission to access this resource. Please contact your administrator for assistance.`
- After that, ordinary role rules apply: a `pending` account's key is refused by user-level
  endpoints (`backend/open_webui/utils/auth.py:567-576`).
- Each key request updates the account's last-active time (`backend/open_webui/utils/auth.py:563`).

### 5.14 Admin: Changing the Authentication Settings

1. Open **Settings**, then **Authentication** under **Admin → System**. The panel is titled
   **Authentication** and has the sections **User Access**, **Pending Accounts**, **LDAP** and
   **OAuth / OIDC** (`src/lib/components/admin/Settings/Authentication.svelte:133-135`, `:139-142`,
   `:255-257`, `:310`, `:546-549`; `src/lib/i18n/locales/en-US/translation.json:2118-2121`, `:2124`).
2. On opening, the panel loads the admin settings, the group list, the LDAP server settings, the
   OAuth settings and the LDAP switch (`src/lib/components/admin/Settings/Authentication.svelte:109-129`).
3. **Save** sends three saves in turn: User Access and Pending Accounts
   (`/api/v1/auths/admin/config`), the LDAP switch and, when LDAP is on, the LDAP server
   (`/admin/config/ldap`, `/admin/config/ldap/server`), and OAuth when it is editable
   (`src/lib/components/admin/Settings/Authentication.svelte:58-107`).
4. When all three succeed it shows `Settings saved successfully!` and reloads the configuration; any
   refusal appears as a pop-up with the server's text and the success message is not shown
   (`src/lib/components/admin/Settings/Authentication.svelte:69-72`, `:79-82`, `:91-94`, `:103-106`).
5. The server silently ignores an unknown **Default User Role** and a **JWT Expiration** it cannot
   read, while still answering success (`backend/open_webui/routers/auths.py:1283-1293`). Accepted
   expiration values are `-1`, `0`, or one number followed by one unit `ms`, `s`, `m`, `h`, `d` or
   `w` (for example `30m`, `12h`, `4w`); a combination such as `1h30m` is ignored. The field keeps
   showing whatever was typed until the panel is opened again, because the panel does not reload
   its values after saving (`src/lib/components/admin/Settings/Authentication.svelte:89-96`).
6. When **Group Mapping** is on and **Group Attribute** is blank, the panel fills in `memberOf`
   before saving (`src/lib/components/admin/Settings/Authentication.svelte:62-67`). **Label**, **Host**, **Attribute for Mail**,
   **Attribute for Username** and **Search Base** are required by both the form and the server
   (`src/lib/components/admin/Settings/Authentication.svelte:325-330`, `:339-344`, `:407-412`, `:426-431`, `:441-446`;
   `backend/open_webui/routers/auths.py:1325-1340`).
7. Changes apply from the next request; existing sessions are not touched. A new **JWT Expiration**
   applies to sign-ins made after the change.

Each setting is listed in section 7.

### 5.15 Admin: Creating an Account for Someone

The admin user list's **Add User** screen (described in `users-groups-roles-and-permissions.md`)
calls `POST /api/v1/auths/add`. The server checks the email shape and that the email is unused,
applies the password rules, creates the account with the chosen role, adds the default group and
publishes `user.created` (`backend/open_webui/routers/auths.py:1101-1163`). The new person signs in
with the email and password the admin chose; no email is sent to them (ground truth).

## 6. Data Model

This section describes what is stored, not live contents. No database was queried. Row contents
(people, emails, keys) are personal or secret data and are not reproduced anywhere in this
knowledgebase.

### 6.1 The `auth` Table

One row per account that can sign in with a password, created in the same transaction as the
`user` row (`backend/open_webui/models/auths.py:26-34`, `:104-142`).

| Column | Meaning | Notes |
|---|---|---|
| `id` | Same value as `user.id` | `backend/open_webui/models/auths.py:31` |
| `email` | The sign-in email, kept in step with `user.email` when an admin changes it | `backend/open_webui/models/auths.py:32`, `:196-210` |
| `password` | The password credential | How it is stored is security-sensitive and not described here |
| `active` | Whether the credential may be used | The application writes only `True` (`backend/open_webui/models/auths.py:120-125`); an inactive row is refused like a wrong password (`backend/open_webui/models/auths.py:159-161`) |

Accounts created by SCIM have no `auth` row, so the email form refuses them
(`backend/open_webui/models/auths.py:158-161`; SCIM in `sso-oauth-oidc-and-scim.md`). Deleting an
account removes both rows (`backend/open_webui/models/auths.py:228-239`).

### 6.2 Columns of the `user` Table Used Here

Full table in `users-groups-roles-and-permissions.md` (`backend/open_webui/models/users.py:144-178`).

| Column | Role in this area | Source |
|---|---|---|
| `id` | Identifies the account inside the session token | `backend/open_webui/routers/auths.py:191-194` |
| `email` | Unique; sign-in lookups ignore letter case | `backend/open_webui/models/users.py:149`, `:438-450` |
| `role` | `admin`, `user` or `pending`; column default `pending` | `backend/open_webui/models/users.py:151` |
| `name` | Shown after sign-in and on the pending overlay (for the admin contact) | `backend/open_webui/models/users.py:152`; `backend/open_webui/routers/auths.py:1184-1189` |
| `profile_image_url` | Set at sign-up to an initials picture; validated on save | `backend/open_webui/models/users.py:155`; `backend/open_webui/utils/validate.py:35-96` |
| `timezone` | Taken from the browser at every sign-in and page load | `backend/open_webui/routers/auths.py:356-378`; `src/routes/auth/+page.svelte:58-62`; `src/routes/+layout.svelte:1294-1298` |
| `oauth`, `scim` | Links to single sign-on and SCIM identities | `backend/open_webui/models/users.py:172-173`; `sso-oauth-oidc-and-scim.md` |
| `last_active_at` | Updated on authenticated requests, at most once per interval per account per server process (`DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL`, default 60 seconds) | `backend/open_webui/utils/auth.py:481-483`, `:563`; `backend/open_webui/models/users.py:771-775`; `backend/open_webui/env.py:362-364` |
| `created_at` | The earliest-created account is the default admin contact on the pending overlay | `backend/open_webui/models/users.py:178`, `:715-720` |
| `username` | Exists, but no sign-in path in this area sets it | `backend/open_webui/models/users.py:150`, `:376-386` |

### 6.3 The `api_key` Table

| Column | Meaning | Source |
|---|---|---|
| `id` | Row id, derived from the account id | `backend/open_webui/models/users.py:244`, `:875` |
| `user_id` | The owning account | `backend/open_webui/models/users.py:245` |
| `key` | The key itself (unique) | `backend/open_webui/models/users.py:246` |
| `data`, `expires_at`, `last_used_at` | Present in the schema; no code in this area writes them | `backend/open_webui/models/users.py:247-249`, `:870-883` |
| `created_at`, `updated_at` | When the key was created | `backend/open_webui/models/users.py:250-251`, `:873-879` |

- **One key per account.** Creating a key deletes the account's existing row first
  (`backend/open_webui/models/users.py:870-883`); deleting removes it
  (`backend/open_webui/models/users.py:885-889`).
- A key is resolved by joining to the `user` table, so it stops working when its account is
  deleted even though the account-deletion path does not remove the `api_key` row
  (`backend/open_webui/models/users.py:425-436`, `:849-863`).
- How keys are stored is security-sensitive and not described further.

### 6.4 Settings Rows

The settings in section 7 are rows of the `config` table, one per dotted key; after first boot the
stored value wins over the environment (ground truth). Keys in this area: `ui.enable_signup`,
`ui.enable_login_form`, `ui.enable_password_change_form`, `ui.default_user_role`,
`ui.default_group_id`, `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content`,
`auth.admin.show`, `auth.admin.email`, `auth.enable_api_keys`, `auth.api_key.endpoint_restrictions`,
`auth.api_key.allowed_endpoints`, `auth.jwt_expiry`, the seventeen `ldap.*` keys, and the
`features.api_keys` entry inside `user.permissions` (`backend/open_webui/config.py:3083-3099`,
`:3127-3128`, `:3155-3158`, `:3211-3227`).

### 6.5 What the Browser Keeps

| Where | Name | What it holds | Set and cleared by |
|---|---|---|---|
| Local storage | `token` | The session token, sent with every request as `Authorization: Bearer …` | Set at sign-in (`src/routes/auth/+page.svelte:51-53`, `:150`); removed at sign-out and session expiry (`src/lib/components/layout/Sidebar/UserMenu.svelte:584`; `src/routes/+layout.svelte:942`, `:1310`) |
| Local storage | `redirectPath` | The page to return to after a single sign-on round trip | `src/routes/auth/+page.svelte:69`, `:151`, `:163-165` |
| Cookie (HttpOnly) | `token` | The same session token, with the same expiry | Set by the server at sign-in and at each session check; deleted at sign-out and on any refused session (`backend/open_webui/routers/auths.py:196-207`, `:279-289`, `:985`; `backend/open_webui/utils/auth.py:494-497`) |
| Cookie | `owui-session` | A server session used during single sign-on round trips | `backend/open_webui/main.py:2648-2674`; deleted at sign-out (`backend/open_webui/routers/auths.py:990`) |
| Cookies | `oauth_id_token`, `oauth_session_id` | Single sign-on details | Deleted at sign-out (`backend/open_webui/routers/auths.py:992-995`); see `sso-oauth-oidc-and-scim.md` |
| Cookie | `oui-session` | Nothing in the current code sets it; sign-out deletes it anyway | `backend/open_webui/routers/auths.py:991` |
| Session storage | (all) | Per-tab working data | Cleared at sign-out (`src/lib/apis/auths/index.ts:406`) |

Because the token lives in the browser, a person who signs out, clears the site's data or uses a
private window starts with no session. Several tabs of the same browser share one token
(local storage is shared per site).

### 6.6 Redis (Optional)

When `REDIS_URL` is configured, Redis holds two things for this area: markers for revoked tokens
and per-account revocation times (`backend/open_webui/utils/auth.py:276-346`, `:349-371`), and the
sign-in rate-limit counters (`backend/open_webui/utils/rate_limit.py:35-36`, `:79-93`). A revoked
token's marker expires when the token would have; the per-account marker expires after one
**JWT Expiration** period, or never when tokens have no expiry (`backend/open_webui/utils/auth.py:327-340`,
`:360-367`). Rate-limit counters expire after about four minutes
(`backend/open_webui/utils/rate_limit.py:83-85`). When `ENABLE_STAR_SESSIONS_MIDDLEWARE=True`, the `owui-session` data also
lives in Redis (`backend/open_webui/main.py:2649-2664`; `backend/open_webui/env.py:967`).

## 7. Settings and Configuration

Defaults below are what the code says. **Every live value is data held in the `config` table or
the server environment and is TO BE CONFIRMED for production.** Persistent keys take their
environment value only on first boot; afterwards the stored value wins (ground truth).

### 7.1 Authentication Tab: User Access

Labels and descriptions are the English text from `src/lib/i18n/locales/en-US/translation.json`.

| Label | Description (verbatim) | Key | Code default | Notes | Source |
|---|---|---|---|---|---|
| Default User Role | `Role assigned to new users when they create an account.` | `ui.default_user_role` | `pending` (`DEFAULT_USER_ROLE`) | Choices `pending`, `user`, `admin` | `src/lib/components/admin/Settings/Authentication.svelte:143-155`; `src/lib/i18n/locales/en-US/translation.json:2060-2061`; `backend/open_webui/config.py:1720` |
| Default Group | `Group assigned to new users by default.` | `ui.default_group_id` | empty (`DEFAULT_GROUP_ID`) | Choices `None` or any existing group | `src/lib/components/admin/Settings/Authentication.svelte:157-170`; `src/lib/i18n/locales/en-US/translation.json:2058-2059`; `backend/open_webui/config.py:1722` |
| Login Form | `Show email and password sign-in on the login page. Set up SSO or LDAP before disabling. Disabling also blocks local sign-ups; password API access is unchanged.` | `ui.enable_login_form` | on (`ENABLE_LOGIN_FORM`) | Hides the form and blocks sign-up; see the security note below | `src/lib/components/admin/Settings/Authentication.svelte:172-178`; `src/lib/i18n/locales/en-US/translation.json:2084-2085`; `backend/open_webui/config.py:1666` |
| New Sign Ups | `Allow new users to create accounts.` | `ui.enable_signup` | on (`ENABLE_SIGNUP`), forced off in no-login mode | Switched off automatically when the first admin is created | `src/lib/components/admin/Settings/Authentication.svelte:180-186`; `src/lib/i18n/locales/en-US/translation.json:2088-2089`; `backend/open_webui/config.py:1664`; `backend/open_webui/routers/auths.py:879` |
| API Keys | `Allow users to create API keys for programmatic access.` | `auth.enable_api_keys` | off (`ENABLE_API_KEYS`) | Global switch; also needed by admins | `src/lib/components/admin/Settings/Authentication.svelte:188-194`; `src/lib/i18n/locales/en-US/translation.json:2036-2037`; `backend/open_webui/config.py:2454` |
| API Key Endpoint Restrictions | `Limit API keys to configured endpoints.` | `auth.api_key.endpoint_restrictions` | off (`ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS`, older spelling `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS`) | Shown only when **API Keys** is on | `src/lib/components/admin/Settings/Authentication.svelte:196-208`; `src/lib/i18n/locales/en-US/translation.json:2034-2035`; `backend/open_webui/config.py:2456-2462` |
| Allowed Endpoints | `Comma-separated API paths that API keys can access.` | `auth.api_key.allowed_endpoints` | empty (`API_KEYS_ALLOWED_ENDPOINTS`, older spelling `API_KEY_ALLOWED_ENDPOINTS`) | Placeholder `e.g.) /api/v1/messages, /api/v1/channels`; link `To learn more about available endpoints, visit our documentation.` to the upstream documentation. A path also allows everything below it | `src/lib/components/admin/Settings/Authentication.svelte:210-228`; `src/lib/i18n/locales/en-US/translation.json:2030-2031`; `backend/open_webui/config.py:2464`; `backend/open_webui/utils/auth.py:541-545` |
| JWT Expiration | `Valid time units: 's', 'm', 'h', 'd', 'w' or '-1' for no expiration.` | `auth.jwt_expiry` | `4w` (`JWT_EXPIRES_IN`) | Placeholder `e.g.) "30m","1h", "10d". `; with `-1` a yellow note `No expiration can pose security risks.` appears; the server also accepts `ms` and `0` (section 5.14) | `src/lib/components/admin/Settings/Authentication.svelte:232-252`; `src/lib/i18n/locales/en-US/translation.json:2078-2079`; `backend/open_webui/config.py:2466`; `backend/open_webui/routers/auths.py:1289-1293` |

When `JWT_EXPIRES_IN` is `-1` at start-up the server also logs a warning beginning
`⚠️  SECURITY WARNING: JWT_EXPIRES_IN is set to '-1'` (`backend/open_webui/config.py:2468-2472`).

**Security note on the Login Form switch.** Hiding the login form does not switch off password
sign-in on the server; that needs the environment variable `ENABLE_PASSWORD_AUTH=False`
(`backend/open_webui/config.py:1670`; `backend/open_webui/routers/auths.py:724-728`). How the two
switches interact with each sign-in and sign-up path, and production's values, are
**Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca)**.

### 7.2 Authentication Tab: Pending Accounts

| Label | Description (verbatim) | Key | Code default | Notes | Source |
|---|---|---|---|---|---|
| Admin Details | `Show admin contact details while an account waits for approval.` | `auth.admin.show` | on (`SHOW_ADMIN_DETAILS`) | Controls the `Admin: …` line on the overlay | `src/lib/components/admin/Settings/Authentication.svelte:258-264`; `src/lib/i18n/locales/en-US/translation.json:2024-2025`; `backend/open_webui/config.py:2170` |
| Admin Contact Email | `Email shown in the pending account overlay.` | `auth.admin.email` | none (`ADMIN_EMAIL`) | Shown only when **Admin Details** is on. Placeholder `Leave empty to use first admin user`; when empty the code actually uses the earliest-created account (section 5.5) | `src/lib/components/admin/Settings/Authentication.svelte:266-278`; `src/lib/i18n/locales/en-US/translation.json:2022-2023`; `backend/open_webui/config.py:2172` |
| Pending User Overlay Title | `Custom title shown while an account waits for approval.` | `ui.pending_user_overlay_title` | empty (`PENDING_USER_OVERLAY_TITLE`) | Placeholder `Enter a title for the pending user info overlay. Leave empty for default.` Plain text | `src/lib/components/admin/Settings/Authentication.svelte:280-291`; `src/lib/i18n/locales/en-US/translation.json:2096-2097`; `backend/open_webui/config.py:1724` |
| Pending User Overlay Content | `Custom message shown while an account waits for approval.` | `ui.pending_user_overlay_content` | empty (`PENDING_USER_OVERLAY_CONTENT`) | Placeholder `Enter content for the pending user info overlay. Leave empty for default.` Markdown | `src/lib/components/admin/Settings/Authentication.svelte:293-306`; `src/lib/i18n/locales/en-US/translation.json:2094-2095`; `backend/open_webui/config.py:1726` |

### 7.3 Authentication Tab: LDAP

The server-side settings appear only after **LDAP** is switched on
(`src/lib/components/admin/Settings/Authentication.svelte:310-544`).

| Label | Description (verbatim) | Key | Code default | Field hints (verbatim) | Source |
|---|---|---|---|---|---|
| LDAP | `Allow users to authenticate with an LDAP directory.` | `ldap.enable` | off (`ENABLE_LDAP`) | | `src/lib/components/admin/Settings/Authentication.svelte:311-317`; `src/lib/i18n/locales/en-US/translation.json:2082-2083`; `backend/open_webui/config.py:2788` |
| Label | `Display name for this LDAP connection.` | `ldap.server.label` | `LDAP Server` | `Enter server label`. Not shown on the sign-in page by any code in scope | `src/lib/components/admin/Settings/Authentication.svelte:321-331`; `backend/open_webui/config.py:2790`; `backend/open_webui/main.py:2327-2335` |
| Host | `LDAP server hostname or IP address.` | `ldap.server.host` | `localhost` | `Enter server host` | `src/lib/components/admin/Settings/Authentication.svelte:335-345`; `backend/open_webui/config.py:2792` |
| Port | `LDAP server port.` | `ldap.server.port` | `389` | `Enter server port`; tooltip `Default to 389 or 636 if TLS is enabled` | `src/lib/components/admin/Settings/Authentication.svelte:347-363`; `backend/open_webui/config.py:2794` |
| Application DN | `Bind DN used for directory search.` | `ldap.server.app_dn` | empty (search runs anonymously) | `Enter Application DN`; tooltip `The Application Account DN you bind with for search` | `src/lib/components/admin/Settings/Authentication.svelte:367-381`; `backend/open_webui/routers/auths.py:534-540` |
| Application DN Password | `Password for the bind DN.` | `ldap.server.app_password` | empty | `Enter Application DN Password`. A secret: never copy its value into a ticket | `src/lib/components/admin/Settings/Authentication.svelte:383-393`; `backend/open_webui/config.py:2802` |
| Attribute for Mail | `LDAP attribute used as the user email address.` | `ldap.server.attribute_for_mail` | `mail` | `Example: mail`; tooltip `The LDAP attribute that maps to the mail that users use to sign in.` | `src/lib/components/admin/Settings/Authentication.svelte:397-414`; `backend/open_webui/config.py:2796` |
| Attribute for Username | `LDAP attribute used as the username.` | `ldap.server.attribute_for_username` | `uid` | `Example: sAMAccountName or uid or userPrincipalName`; tooltip `The LDAP attribute that maps to the username that users use to sign in.` | `src/lib/components/admin/Settings/Authentication.svelte:416-433`; `backend/open_webui/config.py:2798` |
| Search Base | `Base DN used when searching for users.` | `ldap.server.users_dn` | empty | `Example: ou=users,dc=foo,dc=example`; tooltip `The base to search for users` | `src/lib/components/admin/Settings/Authentication.svelte:436-448`; `backend/open_webui/config.py:2804` |
| Search Filters | `LDAP filter used to match signing-in users.` | `ldap.server.search_filter` | empty | `Example: (&(objectClass=inetOrgPerson)(uid=%s))`; link `Click here for filter guides.` (ldap.com) | `src/lib/components/admin/Settings/Authentication.svelte:450-466`; `backend/open_webui/config.py:2806` |
| TLS | `Use TLS when connecting to the LDAP server.` | `ldap.server.use_tls` | on | | `src/lib/components/admin/Settings/Authentication.svelte:468-474`; `backend/open_webui/config.py:2808` |
| Certificate Path | `Certificate file used for TLS verification.` | `ldap.server.ca_cert_file` | empty | `Enter certificate path` (a file path on the server). Shown when TLS is on | `src/lib/components/admin/Settings/Authentication.svelte:476-486`; `backend/open_webui/config.py:2810` |
| Validate Certificate | `Verify the LDAP server certificate when TLS is enabled.` | `ldap.server.validate_cert` | on | Shown when TLS is on | `src/lib/components/admin/Settings/Authentication.svelte:488-494`; `backend/open_webui/config.py:2812` |
| Ciphers | `TLS cipher list for LDAP connections.` | `ldap.server.ciphers` | `ALL` | `Example: ALL`; tooltip `Default to ALL`. Shown when TLS is on | `src/lib/components/admin/Settings/Authentication.svelte:496-507`; `backend/open_webui/config.py:2814` |
| Group Mapping | `Map LDAP groups to Open WebUI groups.` | `ldap.group.enable_management` | off | Replaces memberships at each sign-in | `src/lib/components/admin/Settings/Authentication.svelte:513-519`; `src/lib/i18n/locales/en-US/translation.json:2066-2067`; `backend/open_webui/config.py:2816` |
| Auto-Create Groups | `Create missing groups from LDAP groups.` | `ldap.group.enable_creation` | off | Shown when Group Mapping is on | `src/lib/components/admin/Settings/Authentication.svelte:521-528`; `src/lib/i18n/locales/en-US/translation.json:2064-2065`; `backend/open_webui/config.py:2818` |
| Group Attribute | `LDAP attribute containing the user group memberships.` | `ldap.server.attribute_for_groups` | `memberOf` | Tooltip `Default to memberOf` | `src/lib/components/admin/Settings/Authentication.svelte:530-541`; `backend/open_webui/config.py:2820` |

The LDAP descriptions above are in `src/lib/i18n/locales/en-US/translation.json:2038-2045`,
`:2050-2053`, `:2064-2067`, `:2072-2073`, `:2076-2077`, `:2080-2083`, `:2100-2101`, `:2114-2117`, `:2125-2126`
and `:2135-2136`.

**Search Filters pitfall.** The server builds its own match on **Attribute for Username** and then
appends the **Search Filters** text unchanged; it does not replace `%s`
(`backend/open_webui/routers/auths.py:558-563`). A filter copied from the placeholder example,
`(&(objectClass=inetOrgPerson)(uid=%s))`, therefore asks the directory for a literal `%s` and
matches nobody, and every LDAP sign-in fails with `LDAP authentication failed.` A filter without
`%s`, such as `(objectClass=inetOrgPerson)`, behaves as intended.

### 7.4 Authentication Tab: OAuth / OIDC

The fourth section configures single sign-on (provider name and discovery URL, client ID and
secret, redirect URI, scopes, claim names, OAuth sign-up, account merging, auto redirect, allowed
domains, role and group mapping, profile refresh). When the OAuth settings follow the environment,
the section is read-only and shows
`These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.`
with `{{ENV_VAR}}` shown as `ENABLE_OAUTH_PERSISTENT_CONFIG`
(`src/lib/components/admin/Settings/Authentication.svelte:546-876`). Every field is documented in
`sso-oauth-oidc-and-scim.md`.

### 7.5 Environment-Only Settings

These are read from the server environment at start-up and are not stored in the `config` table.

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `WEBUI_AUTH` | `True` | `False` is no-login mode (single-person installations only) | `backend/open_webui/env.py:751` |
| `ENABLE_PASSWORD_AUTH` | `True` | `False` refuses email-and-password and LDAP sign-in on the server | `backend/open_webui/config.py:1670`; `backend/open_webui/routers/auths.py:486-490`, `:724-728` |
| `ENABLE_INITIAL_ADMIN_SIGNUP` | `False` | Allows the first admin to sign up even with the login form hidden | `backend/open_webui/env.py:753`; `backend/open_webui/routers/auths.py:912-914` |
| `ENABLE_SIGNUP_PASSWORD_CONFIRMATION` | `False` | Adds **Confirm Password** to sign-up | `backend/open_webui/env.py:754` |
| `ENABLE_PASSWORD_CHANGE_FORM` | `True` | Seeds `ui.enable_password_change_form` (stored, but no admin screen edits it) | `backend/open_webui/config.py:1668`, `:3085` |
| `PASSWORD_HASH_ALGORITHM` | `bcrypt` | `bcrypt` brings the 72-byte limit; `argon2` is the alternative | `backend/open_webui/env.py:815` |
| `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_VALIDATION_REGEX_PATTERN`, `PASSWORD_VALIDATION_HINT` | `False`, a pattern requiring eight characters with mixed case, a digit and a symbol, empty | The optional password pattern and the message shown when it fails | `backend/open_webui/env.py:814-829` |
| `WEBUI_SECRET_KEY` | none | Signs session tokens; start-up stops if it is empty while authentication is on; changing it ends every session. Never reproduce its value | `backend/open_webui/env.py:762-765`, `:780-788` |
| `WEBUI_AUTH_COOKIE_SAME_SITE`, `WEBUI_AUTH_COOKIE_SECURE` | `lax`, off (inherited from `WEBUI_SESSION_COOKIE_SAME_SITE` and `WEBUI_SESSION_COOKIE_SECURE`) | Flags on the `token` cookie | `backend/open_webui/env.py:769-778` |
| `WEBUI_SESSION_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE` | `lax`, off | Flags on the `owui-session` cookie | `backend/open_webui/env.py:769-770`; `backend/open_webui/main.py:2656-2674` |
| `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` | none | Where the browser goes after signing out (also passed to identity-provider logout) | `backend/open_webui/env.py:864`; `backend/open_webui/routers/auths.py:1031-1034`, `:1049-1057` |
| `WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_PASSWORD`, `WEBUI_ADMIN_NAME` | empty, empty, `Admin` | Create the first admin at start-up when no accounts exist | `backend/open_webui/env.py:798-800`; `backend/open_webui/main.py:376-380` |
| `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` and the name, groups and role header variables | none | Trusted-header mode | `backend/open_webui/env.py:802-805`; `sso-oauth-oidc-and-scim.md` |
| `CUSTOM_API_KEY_HEADER` | `x-api-key` | The extra header a program may use to send an API key | `backend/open_webui/env.py:812` |
| `USER_PERMISSIONS_FEATURES_API_KEYS` | `False` | Seeds the default `features.api_keys` permission | `backend/open_webui/config.py:1924`, `:2003` |
| `REDIS_URL` (and Sentinel or Cluster settings) | none | Enables token revocation and a shared rate-limit count | ground truth; `backend/open_webui/utils/auth.py:285-286`; `backend/open_webui/utils/rate_limit.py:55-61` |
| `ENABLE_STAR_SESSIONS_MIDDLEWARE` | `False` | Keeps `owui-session` data in Redis | `backend/open_webui/env.py:967`; `backend/open_webui/main.py:2649-2664` |
| `ENABLE_OAUTH_TOKEN_EXCHANGE` | off | Enables the token-exchange endpoint | `backend/open_webui/routers/auths.py:1636-1640`; `sso-oauth-oidc-and-scim.md` |
| `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL` | `60` seconds | How often `last_active_at` is written per account per process | `backend/open_webui/env.py:362-364` |
| `PROFILE_IMAGE_ALLOWED_MIME_TYPES`, `PROFILE_IMAGE_MAX_DATA_URI_SIZE` | PNG, JPEG, GIF and WebP; no size cap | Which uploaded profile pictures the server accepts | `backend/open_webui/env.py:971-983`; `backend/open_webui/utils/validate.py:83-91` |
| `WEBUI_NAME` | `MedIT GPT` | The product name in every sign-in title | `backend/open_webui/env.py:951` |

The environment variables that seed the persistent keys in sections 7.1 to 7.3 (`ENABLE_SIGNUP`,
`ENABLE_LOGIN_FORM`, `DEFAULT_USER_ROLE`, `DEFAULT_GROUP_ID`, `PENDING_USER_OVERLAY_TITLE`,
`PENDING_USER_OVERLAY_CONTENT`, `SHOW_ADMIN_DETAILS`, `ADMIN_EMAIL`, `ENABLE_API_KEYS`,
`ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS`, `API_KEYS_ALLOWED_ENDPOINTS`, `JWT_EXPIRES_IN`,
`ENABLE_LDAP` and the `LDAP_*` variables) matter only on first boot.

### 7.6 Wording Can Be Overridden

Admins can store translation overrides (`ui.i18n`). They are sent with `/api/config` before
sign-in and replace the bundled text for any key in that language, so the live wording of the
sign-in page, the pending overlay and these settings may differ from the verbatim text in this
document (`backend/open_webui/main.py:2316`; `src/routes/+layout.svelte:1254`;
`src/lib/i18n/index.ts:16-22`; `src/lib/i18n/settings-translations.ts:4-20`). Whether production
has overrides is **TO BE CONFIRMED**.

## 8. Cron Jobs and Background Processes

There is no crontab and no scheduled job in this area. None of the seven background loops started
by the server (`knowledgebase/tools/inventory.md`) handles authentication. What runs outside the
request itself:

| What | When | Where it runs | Source |
|---|---|---|---|
| First-admin bootstrap from `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` | Once at each server start, only if no account exists | Server start-up | `backend/open_webui/main.py:376-380`; `backend/open_webui/utils/auth.py:634-665` |
| Secret-key check | At start-up; stops the server if `WEBUI_SECRET_KEY` is empty while authentication is on | Server start-up | `backend/open_webui/env.py:780-788` |
| `last_active_at` update | After authenticated requests, as a fire-and-forget task, at most once per 60 seconds per account per process | In-process task | `backend/open_webui/utils/auth.py:481-483`, `:563`; `backend/open_webui/models/users.py:771-775` |
| Event delivery (webhooks and Event functions) | After each sign-in, sign-up, sign-out, password change and API-key change | In-process tasks | `backend/open_webui/events.py:1062-1071`, `:1159-1171`, `:1174-1202` |
| Disconnecting live connections | When a token is revoked (sign-out or password change, Redis only) or a role changes | In-process | `backend/open_webui/utils/auth.py:342-346`, `:369-371`; `backend/open_webui/events.py:1089-1100`; `backend/open_webui/socket/main.py:388-404` |
| Rate-limit clean-up | No loop: old in-memory buckets are pruned at each check; Redis buckets expire on their own | At check time | `backend/open_webui/utils/rate_limit.py:41-45`, `:83-85` |
| Token-expiry check | Every 15 seconds and when a tab becomes visible | In the person's **browser**, not on the server | `src/routes/+layout.svelte:1182-1183`, `:1227-1231` |

Saving the Authentication tab writes the settings immediately (`Config.upsert`); nothing is queued
(`backend/open_webui/routers/auths.py:1295`, `:1345`, `:1360`, `:1513`).

## 9. Notifications and Emails

**No email.** The application sends no email (ground truth). In this area that means: no sign-up
confirmation, no "your account was approved" message, no password-reset email, and no message to
admins when someone signs up. Admins learn about new `pending` accounts only by looking at the
admin user list, or through an event webhook they set up (below). The in-app notification channel
is not used for any authentication event (`backend/open_webui/events.py:669-675`, `:1083-1086`).

**Pop-ups (toasts).** Every pop-up in this area is listed in section 10. The successful ones are
`You're now logged in.`, `Password updated. Please sign in again.`, `API Key created.`,
`API Key deleted.` and `Settings saved successfully!`.

**Events.** Each action below publishes an event to every configured event webhook that
subscribes to it and to any active Event function (`backend/open_webui/events.py:1171-1202`;
event webhooks are documented in `notifications-webhooks-events-and-banners.md`).

| Event | Webhook message | Published when | Source |
|---|---|---|---|
| `auth.signup` | `User signed up` | Self-service sign-up (including the first admin); its data carries the new email | `backend/open_webui/events.py:99-101`; `backend/open_webui/routers/auths.py:939-946` |
| `auth.login` | `User logged in` | Every successful sign-in, and the automatic sign-in that follows a sign-up; the source records the method (`password`, `ldap`, `trusted_header`, `oauth`, `system`, or `api` after sign-up) | `backend/open_webui/events.py:102-104`; `backend/open_webui/routers/auths.py:173`, `:210-218`, `:702`, `:831`, `:947`, `:1771` |
| `auth.logout` | `User logged out` | Sign-out when the browser presented a token | `backend/open_webui/events.py:105-107`; `backend/open_webui/routers/auths.py:970-983` |
| `auth.password_changed` | `Password changed` | Successful self-service password change | `backend/open_webui/events.py:108-110`; `backend/open_webui/routers/auths.py:410-418` |
| `auth.api_key.created` | `API key created` | A key was created or replaced | `backend/open_webui/events.py:111-113`; `backend/open_webui/routers/auths.py:1538-1545` |
| `auth.api_key.deleted` | `API key deleted` | A key was deleted | `backend/open_webui/events.py:114-116`; `backend/open_webui/routers/auths.py:1560-1567` |
| `auth.oauth_session.deleted` | `OAuth session deleted` | A tool-server OAuth session was disconnected | `backend/open_webui/events.py:117-119`; `backend/open_webui/routers/auths.py:1085-1092` |
| `user.created` | `User created` | Any new account from sign-up, LDAP, trusted header or **Add User**; the source records which | `backend/open_webui/events.py:120-122`; `backend/open_webui/routers/auths.py:675-682`, `:887-894`, `:1137-1144` |
| `user.updated` | `User updated` | The browser recorded its time zone, which happens at **every** sign-in and page load | `backend/open_webui/events.py:123-125`; `backend/open_webui/routers/auths.py:369-375`; `src/routes/+layout.svelte:1294-1298` |
| `user.profile_updated` | `User profile updated` | Profile saved in **Settings → Account** | `backend/open_webui/events.py:138-140`; `backend/open_webui/routers/auths.py:332-339` |
| `user.role_updated` | `User role updated` | A trusted-header role header changed the role at sign-in | `backend/open_webui/events.py:129-131`; `backend/open_webui/routers/auths.py:777-784` |

Webhook messages have the account id appended in brackets (`backend/open_webui/events.py:1039-1044`),
and every event payload names the acting person by id, name, email and role
(`backend/open_webui/events.py:704`, `:974-985`). Webhook deliveries of these events are
therefore personal data. A webhook subscribed to `user.updated` receives one delivery per page load
per person.

**Live connection.** Revoking tokens (sign-out or password change, with Redis) and changing a role
disconnect the account's live connections, which then reconnect by themselves
(`backend/open_webui/socket/main.py:388-404`). If reconnection takes longer than about two
seconds on a visible page, the app may show `Connection lost. Reconnecting...` and later
`Reconnected` (`src/routes/+layout.svelte:129`, `:147-163`, `:184-196`).

**Browser notifications.** None in this area.

## 10. Error, Warning and Notice Messages (Verbatim)

How server text reaches people: the sign-in page, the Account tab and the Authentication tab show
the server's `detail` text unchanged in a red pop-up (`src/routes/auth/+page.svelte:74-77`,
`:90-95`, `:101-104`; `src/lib/components/chat/Settings/Account.svelte:158-160`, `:191-194`;
`src/lib/components/admin/Settings/Authentication.svelte:69-72`, `:91-94`). Validation errors
(HTTP 422) are unpacked only by the profile-save helper, which joins their texts with `; `
(`src/lib/apis/auths/index.ts:499-503`); everywhere else in this area they would print as the
words [object Object]. Placeholders are written `{name}` using the source's variable name.

### 10.1 Messages from the Server

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The email or password provided is incorrect. Please check for typos and try logging in again.` | Error (HTTP 400) | `backend/open_webui/constants.py:60`; raised at `backend/open_webui/routers/auths.py:833` (sign-in), `:498` (LDAP with a blank password), `:344`, `:378`, `:423` (no session; not expected from the app) | Email-and-password sign-in with an unknown email, a wrong password, an account that has no usable local password (single sign-on, LDAP or SCIM accounts) or an inactive credential. Some single sign-on failures also show it (`sso-oauth-oidc-and-scim.md`) | Retype carefully (Caps Lock; the eye button shows the password); use the method the account was created with | Ask which sign-in method they normally use; ask an admin to confirm the account and its exact email in the admin user list. Tier 1 cannot reset passwords |
| `API rate limit exceeded` | Error (HTTP 429) | `backend/open_webui/constants.py:87`; `backend/open_webui/routers/auths.py:818-822`, `:1642-1648` | More than 15 email-and-password attempts for one email address within three to four minutes, counting successful and refused attempts; also the token-exchange limit | Stop trying for at least four minutes, then try once, carefully | Ask how many attempts and whether a password manager, script or shared login retries automatically. If it persists after a quiet period, escalate with the email address and times |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403 at sign-in and LDAP; 400 otherwise) | `backend/open_webui/constants.py:73`; `backend/open_webui/routers/auths.py:724-728`, `:486-490`, `:394-395`, `:1195-1196` | Password or LDAP sign-in while `ENABLE_PASSWORD_AUTH=False`; **Change Password** in trusted-header mode; the admin-contact lookup while **Admin Details** is off (the overlay hides that one) | Use the sign-in method the organization provides | Confirm which sign-in methods production offers (TO BE CONFIRMED); escalate if password sign-in is meant to work |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403 for sign-up and API keys; HTTP 401 for role checks) | `backend/open_webui/constants.py:70-72`; `backend/open_webui/routers/auths.py:909-911`, `:913-914`, `:916-917`, `:1676-1679`, `:1726-1730`; `backend/open_webui/utils/auth.py:546-550`, `:567-576`, `:625-631` | Sign-up while **New Sign Ups** or **Login Form** is off (or, on first run, with the login form hidden); a `pending` account calling a user-level endpoint or a non-admin calling an admin one; an API key used outside **Allowed Endpoints**; a refused token exchange | For sign-up, ask for an account through the organization's process; for API keys, call an allowed endpoint | Check the person's role and, with an admin, the sign-up switches or endpoint restrictions |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/constants.py:59`; `backend/open_webui/utils/auth.py:455-460`, `:513-517`; `backend/open_webui/routers/auths.py:273-277` | A session token whose account no longer exists; an API key that is unknown (deleted or replaced); the session check's own expiry test (an expired token normally gives `401 Unauthorized` first) | Sign in again; for programs, use the current key | If it appears straight after signing in, ask an admin whether the account was deleted or recreated |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/constants.py:69`; `backend/open_webui/utils/auth.py:489-493` | A session token that has expired or cannot be read, for example after the server's secret key changed | Sign in again | Many people at once points to a secret-key change or redeploy: escalate |
| `Invalid token` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:449-453` (the same text at `:443-446` and `backend/open_webui/main.py:2243-2246` cannot occur, because the token reader never raises) | A token revoked through Redis: after a password change or admin reset, an identity-provider logout, or a sign-out with that token | Sign in again | Ask whether the password was just changed or reset |
| `Not authenticated` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:415-416` | A request with no session token, cookie or API key, typically from a program | Send the API key (section 5.13) | Check that the program sends its key |
| `User mismatch. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:462-468` | Trusted-header mode: the proxy now reports a different email from the stored session | Sign out and sign in again | See `sso-oauth-oidc-and-scim.md` |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400) | `backend/open_webui/constants.py:46`; `backend/open_webui/routers/auths.py:922-923`, `:1112-1113` | Sign-up or **Add User** with an email that already has an account (any letter case) | Sign in instead | Confirm with an admin; if sign-in also fails, follow 11.1 |
| `The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com).` | Error (HTTP 400) | `backend/open_webui/constants.py:61`; `backend/open_webui/routers/auths.py:919-920`, `:1109-1110` | Sign-up or **Add User** with an address that has no dot after the `@`. The browser's own email check lets some of these through, for example `jane.doe@example` | Type the full address, for example `jane.doe@example.com` | None needed |
| `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | Error (HTTP 400) | `backend/open_webui/constants.py:48-50`; `backend/open_webui/utils/auth.py:191-195`; reached through `backend/open_webui/routers/auths.py:926-929`, `:404-407`, `:1116-1119` and `backend/open_webui/routers/users.py:962-966` | A new password over 72 bytes while the algorithm is `bcrypt` | Choose a shorter password, or fewer accented letters and emoji | Explain bytes versus characters (section 5.10) |
| `The password does not meet the required validation criteria.` | Error (HTTP 400) | `backend/open_webui/constants.py:114`; `backend/open_webui/utils/auth.py:197-199` | The optional password pattern is on, no hint is configured, and the new password fails it | Try a longer password mixing upper- and lower-case letters, digits and a symbol | The rule in force is TO BE CONFIRMED; ask the platform maintainer |
| `{PASSWORD_VALIDATION_HINT}` | Error (HTTP 400) | `backend/open_webui/constants.py:114`; `backend/open_webui/utils/auth.py:199`; `backend/open_webui/env.py:829` | Same as above when the operator wrote a hint: the hint text itself is the message | Follow the hint | None needed |
| `The password provided is incorrect. Please check for typos and try again.` | Error (HTTP 400) | `backend/open_webui/constants.py:62`; `backend/open_webui/routers/auths.py:421` | **Change Password** with a wrong current password, including every single sign-on and LDAP account (they have no known local password) | Retype; single sign-on and LDAP users change their password with their identity provider | Ask how the person signs in |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500) | `backend/open_webui/constants.py:43`; `backend/open_webui/routers/auths.py:871-872`, `:1157-1158` (and `:660-661`, which LDAP replaces with its generic message) | The database did not return the new account | Try again later | Escalate with the time; the support contact the message mentions is TO BE CONFIRMED |
| `Your provider has not provided a trusted header. Please contact your administrator for assistance.` | Error (HTTP 400) | `backend/open_webui/constants.py:63-65`; `backend/open_webui/routers/auths.py:734-735` | Trusted-header mode, but the request arrived without the email header | Contact the administrator | See `sso-oauth-oidc-and-scim.md`; escalate |
| `You can't turn off authentication because there are existing users. If you want to disable WEBUI_AUTH, make sure your web interface doesn't have any existing users and is a fresh installation.` | Error (HTTP 400) | `backend/open_webui/constants.py:67`; `backend/open_webui/routers/auths.py:800-801` | No-login mode switched on for an installation that already has accounts; appears on the sign-in page's automatic sign-in | None | Server configuration error: escalate |
| `Use of API key is not enabled in the environment.` | Error (HTTP 403) | `backend/open_webui/constants.py:81`; `backend/open_webui/utils/auth.py:526-536` | A program uses an API key while **API Keys** is off, or the key's owner is not an admin and lacks `features.api_keys` | Ask an admin | Ask an admin to check the switch and the person's permission (directly or through a group) |
| `API key creation is not allowed in the environment.` | Error (HTTP 403) | `backend/open_webui/constants.py:93`; `backend/open_webui/routers/auths.py:1517-1525` | Creating, reading or deleting a key with the switch off or without the permission | None | As above; the Account tab normally hides the section in this case, so it is usually a stale page or a program |
| `Oops! It looks like there's a hiccup. The API key is missing. Please make sure to provide a valid API key to access this feature.` | Error (HTTP 404) | `backend/open_webui/constants.py:80`; `backend/open_webui/routers/auths.py:1572-1581` | Reading the key when none exists; the Account tab treats this as "no key yet" and shows nothing | None | None |
| `Oops! Something went wrong while creating your API key. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500) | `backend/open_webui/constants.py:92`; `backend/open_webui/routers/auths.py:1549-1550` | Saving the key reported failure; the save routine in the code always reports success, so this is not expected | Try again | Escalate |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/constants.py:16-18`; `backend/open_webui/routers/auths.py:341-342` | Saving the profile found no account to update | Reload and retry | Escalate if repeated |
| `LDAP authentication is not enabled` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:483-484` | LDAP sign-in attempted while LDAP is off, for example a sign-in page opened before an admin switched LDAP off | Reload the sign-in page and use what it offers | None |
| `Failed to configure TLS for LDAP connection.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:515-524` | The LDAP TLS settings (certificate path, ciphers) cannot be used | None | Escalate: LDAP TLS settings; the log has `TLS configuration error: {e}` |
| `LDAP authentication failed.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:707-709` | Any failure after the LDAP connection starts: application bind refused, user not found, no email in the directory, wrong directory password, username mismatch, account creation failure, no active local credential for the email | Check the username and password; try once more | Note the time; an admin or the maintainer reads the log line `LDAP authentication error: {e}` (section 10.3) for the real reason; check the Search Filters pitfall (section 7.3) |
| `Application account bind failed` | Log only (replaced by `LDAP authentication failed.`) | `backend/open_webui/routers/auths.py:541-542` | The **Application DN** and its password were refused by the directory | None | Escalate: LDAP application account |
| `User not found in the LDAP server` | Log only (replaced) | `backend/open_webui/routers/auths.py:564-565` | No directory entry matched the username, **Search Base** and **Search Filters** | Check the username format expected (TO BE CONFIRMED) | Escalate with the username format used |
| `User does not have a valid email address.` | Log only (replaced) | `backend/open_webui/routers/auths.py:578-579` | The directory entry has no value in **Attribute for Mail** | None | Escalate: directory data |
| `Authentication failed.` | Log only (replaced) | `backend/open_webui/routers/auths.py:644-645` | The directory refused the person's password | Retype the directory password | None beyond 11.6 |
| `Internal error occurred during LDAP user creation.` | Log only (replaced) | `backend/open_webui/routers/auths.py:684-688` | Creating the MedIT GPT account for a new LDAP user failed (log `LDAP user creation error: {err}`) | None | Escalate |
| `User record mismatch.` | Log only (replaced) | `backend/open_webui/routers/auths.py:705-706` | The typed username is not among the entry's username values (the search matched on something else) | None | Escalate: LDAP attribute settings |
| `An internal error occurred during signup.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:948-952` | Unexpected error while creating the account (log `Signup error: {err}`) | Try again later | Escalate with the time |
| `Failed to sign out from the OpenID provider.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1041-1047` | Single sign-on sign-out could not read the identity provider's settings; from the user menu nothing visible happens | Try again later; on a shared computer, clear the browser's data for the site, which removes the stored token (section 6.5) | See `sso-oauth-oidc-and-scim.md`; escalate |
| `No OAuth session found for this provider` | Error (HTTP 404) | `backend/open_webui/routers/auths.py:1079-1084` | Disconnecting a tool-server sign-in that no longer exists | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `An internal error occurred while adding the user.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1159-1163` | Unexpected error during **Add User** (log `Add user error: {err}`) | Admin retries | Escalate |
| `Required field {name} is empty` | Error (HTTP 400) | `backend/open_webui/constants.py:131`; `backend/open_webui/routers/auths.py:1332-1340` | Saving LDAP settings with `label`, `host`, `attribute_for_mail`, `attribute_for_username` or `search_base` empty, or `attribute_for_groups` empty while Group Mapping is on; `{name}` is that internal field name | Admin fills the field | None |
| `I18N must be a dictionary` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1242-1246` | Saving admin settings with the translation-override block sent as empty (null) rather than as a list of languages; shown as [object Object] | None | See `admin-settings-panels.md` |
| `Invalid language: {locale}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1254-1255` | Translation overrides with a blank or reserved language name; shown as [object Object] | None | See `admin-settings-panels.md` |
| `Invalid translation key: {key}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1258-1259` | Translation overrides with a blank or reserved key; shown as [object Object] | None | See `admin-settings-panels.md` |
| `Interpolation placeholders do not match: {locale}: {key}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1260-1262` | A translation override drops or renames a `{{placeholder}}`; shown as [object Object] | None | See `admin-settings-panels.md` |
| `Token exchange is disabled` | API error (HTTP 403) | `backend/open_webui/routers/auths.py:1636-1640` | A program called token exchange while `ENABLE_OAUTH_TOKEN_EXCHANGE` is off | None | See `sso-oauth-oidc-and-scim.md` |
| `Provider '{name}' is not configured` | API error (HTTP 404) | `backend/open_webui/constants.py:132`; `backend/open_webui/routers/auths.py:1652-1665` | Token exchange named a provider that is not set up | None | See `sso-oauth-oidc-and-scim.md` |
| `Unable to determine which client the token was issued to` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1667-1673` | Token exchange with a trusted-client list, when the provider cannot say which client the token belongs to | None | See `sso-oauth-oidc-and-scim.md` |
| `Invalid token or unable to fetch user info` | Replaced | `backend/open_webui/routers/auths.py:1686-1690` | Raised inside a block whose catch-all replaces it with the next message | None | None |
| `Invalid token or unable to validate with provider` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1691-1696` | The provider would not confirm the token during token exchange | None | See `sso-oauth-oidc-and-scim.md` |
| `Token missing required 'sub' claim` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1704-1709` | Token exchange: the provider's answer has no subject identifier | None | See `sso-oauth-oidc-and-scim.md` |
| `Token missing required email claim` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1713-1718` | Token exchange: the provider's answer has no email | None | See `sso-oauth-oidc-and-scim.md` |
| `User not found. Please sign in via the web interface first.` | API error (HTTP 403) | `backend/open_webui/routers/auths.py:1748-1752` | Token exchange for a person who has never signed in on the website | Sign in on the website once | See `sso-oauth-oidc-and-scim.md` |
| `Invalid image URL.` | Error (HTTP 422) | `backend/open_webui/utils/validate.py:56-57` | A profile picture value that is not text (programs only) | None | None |
| `Invalid profile image URL: HTTP(S) URLs must include a host.` | Error (HTTP 422) | `backend/open_webui/utils/validate.py:78-80` | Saving a profile picture link such as `https:///x.png` | Use a complete link or upload a photo | None |
| `Invalid profile image URL: data URI exceeds the {PROFILE_IMAGE_MAX_DATA_URI_SIZE}-byte limit.` | Error (HTTP 422) | `backend/open_webui/utils/validate.py:86-90` | An uploaded photo larger than the operator's cap (no cap by default) | Use a smaller photo | None |
| `Invalid profile image URL: must be a known internal path, an HTTP(S) URL with a host, or a data:image URI (png/jpeg/gif/webp).` | Error (HTTP 422) | `backend/open_webui/utils/validate.py:93-96` | Saving a profile picture of another kind (for example SVG) | Upload a PNG, JPEG, GIF or WebP | None |
| `Invalid background image URL: must reference an internal file.` | Error | `backend/open_webui/utils/validate.py:59-62` | Model background images, not this area | None | See `workspace-models-and-model-access.md` |
| `Background image must be at most 5 MiB.` | Error | `backend/open_webui/utils/validate.py:105-106` | Model background images | None | See `workspace-models-and-model-access.md` |
| `Background image must be PNG, JPEG, WebP, or GIF.` | Error | `backend/open_webui/utils/validate.py:110-111` | Model background images | None | See `workspace-models-and-model-access.md` |
| `Background image must be at most 25 megapixels.` | Error | `backend/open_webui/utils/validate.py:112-113` | Model background images | None | See `workspace-models-and-model-access.md` |
| `Invalid background image.` | Error | `backend/open_webui/utils/validate.py:118-119` | Model background images | None | See `workspace-models-and-model-access.md` |

The profile-picture messages appear in **Settings → Account** preceded by the words "Value error,"
which the validation library adds (they are not in the repository), because the profile-save
helper joins validation texts
(`src/lib/apis/auths/index.ts:499-503`; `backend/open_webui/models/users.py:279-282`).

### 10.2 Messages from the Browser

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You're now logged in.` | Success | `src/routes/auth/+page.svelte:50` | Any successful sign-in from `/auth` (password, LDAP, sign-up, return from single sign-on, automatic sign-in) | None | None |
| `Passwords do not match.` | Error | `src/routes/auth/+page.svelte:83-88` | Sign-up with **Confirm Password** enabled and the two entries different | Retype both | None |
| `Signing in to {{WEBUI_NAME}}` | Notice (with a spinner) | `src/routes/auth/+page.svelte:235-248` | Trusted-header or no-login mode, while signing in automatically; `{{WEBUI_NAME}}` shows `MedIT GPT` | Wait | If it never finishes, escalate (`sso-oauth-oidc-and-scim.md`) |
| `does not make any external connections, and your data stays securely on your locally hosted server.` | Notice | `src/routes/auth/+page.svelte:286-293` | First run only, after the symbol ⓘ and the product name; upstream wording | None | Never shown once accounts exist |
| `Session expired. Please sign in again.` | Error | `src/routes/+layout.svelte:948` | The token is within 60 seconds of its expiry, or a refused request is confirmed by a refused session check, or a stored token is refused at page load | Sign in again | How often? Compare with **JWT Expiration**; follow 11.7 |
| `Connection lost. Reconnecting...` | Warning | `src/routes/+layout.svelte:162` | The live connection has been down for more than about two seconds on a visible page, including just after tokens are revoked or a role changes | Wait | Connectivity issue if frequent |
| `Reconnected` | Success | `src/routes/+layout.svelte:194` | The live connection came back after the warning above | None | None |
| `Account Activation Pending` | Notice (overlay title) | `src/lib/components/layout/Overlay/AccountPending.svelte:34` | A `pending` account with no custom overlay title | Wait for approval, then press **Check Again** | Ask an admin to approve (`users-groups-roles-and-permissions.md`) |
| `Contact Admin for WebUI Access` | Notice (overlay title, second line) | `src/lib/components/layout/Overlay/AccountPending.svelte:35` | As above | As above | As above |
| `Your account status is currently pending activation.` | Notice (overlay message) | `src/lib/components/layout/Overlay/AccountPending.svelte:48` | A `pending` account with no custom overlay content | As above | As above |
| `To access the WebUI, please reach out to the administrator. Admins can manage user statuses from the Admin Panel.` | Notice (overlay message) | `src/lib/components/layout/Overlay/AccountPending.svelte:48-50` | As above | Contact the administrator (the official route is TO BE CONFIRMED) | As above |
| `Admin: {name} ({email})` | Notice | `src/lib/components/layout/Overlay/AccountPending.svelte:54-58` | `pending` account while **Admin Details** is on; `{name}` can be empty (section 5.5) | Contact that admin if appropriate | The shown person is live data |
| `Password updated. Please sign in again.` | Success | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:25-27` | The password change was accepted; the browser then signs out | Sign in with the new password | None |
| `The passwords you entered don't quite match. Please double-check and try again.` | Error | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:41-44` | **New Password** and **Confirm Password** differ | Retype both | None |
| `API Key created.` | Success | `src/lib/components/chat/Settings/Account.svelte:184` | A key was created or replaced | Copy it into the program that needs it | None |
| `Failed to create API Key.` | Error | `src/lib/components/chat/Settings/Account.svelte:186` | The server answered success without a key (not expected). A real refusal shows no message at all (section 5.12) | Reload the tab and try again | If nothing happens, check the switch and permission with an admin |
| `API Key deleted.` | Success | `src/lib/components/chat/Settings/Account.svelte:198` | The key was deleted | Update any program that used it | None |
| `Delete API Key?` | Confirmation title | `src/lib/components/chat/Settings/Account.svelte:583-587` | **Delete** chosen from the key's `More` menu | Confirm or cancel | Programs using the key stop working |
| `This will revoke the current API key.` | Confirmation text | `src/lib/components/chat/Settings/Account.svelte:589-591` | As above | As above | As above |
| `Variable keys must use lowercase snake case.` | Error | `src/lib/components/chat/Settings/Account.svelte:96`, `:127` | User Variables in the Account tab (`user-settings-and-personalisation.md`) | Use names like `team_name` | None |
| `Variable keys must be unique.` | Error | `src/lib/components/chat/Settings/Account.svelte:100`, `:130` | As above | Rename the duplicate | None |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:848` | The Account tab's **Save** stored the profile and variables | None | None |
| `Settings saved successfully!` | Success | `src/lib/components/admin/Settings/Authentication.svelte:103-106` | All three Authentication-tab saves succeeded (it does not prove an unreadable **JWT Expiration** was stored; section 5.14) | None | None |
| `No expiration can pose security risks.` | Warning | `src/lib/components/admin/Settings/Authentication.svelte:243-251` | **JWT Expiration** is exactly `-1` | Admin decides | Policy question for the platform maintainer |
| `These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.` | Notice | `src/lib/components/admin/Settings/Authentication.svelte:550-559` | OAuth settings follow the environment; `{{ENV_VAR}}` shows `ENABLE_OAUTH_PERSISTENT_CONFIG` | None | See `sso-oauth-oidc-and-scim.md` |
| `Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.` | Info (shown for 10 seconds) | `src/lib/components/chat/Settings/Account/UserProfileImage.svelte:146-158`, `:220-232` | **Initials** chosen in a browser that blocks reading drawn images (privacy or anti-fingerprinting protection) | Upload a photo, or keep the default picture | None |
| `{{webUIName}} Backend Required` | Error (page title) | `src/routes/error/+page.svelte:25` | The app could not read `/api/config` at start-up; `{{webUIName}}` shows `MedIT GPT` | Press **Check Again** later | Service outage or network block: escalate with the time |
| `Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.` | Error (page text) | `src/routes/error/+page.svelte:28-31` | As above; the wording assumes a developer setup, but for a user it usually means the server could not be reached | As above | As above; the page's links point to the upstream project (`src/routes/error/+page.svelte:35-43`) |

### 10.3 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `LDAP authentication error: {e}` | Log (error) | `backend/open_webui/routers/auths.py:708` | Every LDAP failure that shows `LDAP authentication failed.`; `{e}` reads `400: ` (or `500: `) followed by the specific reason from section 10.1 | None | The maintainer matches the time of the attempt |
| `TLS configuration error: {e}` | Log (error) | `backend/open_webui/routers/auths.py:523` | Behind `Failed to configure TLS for LDAP connection.` | None | Escalate |
| `LDAP user creation error: {err}` | Log (error) | `backend/open_webui/routers/auths.py:687` | Account creation for a new LDAP user failed | None | Escalate |
| `Failed to sync groups for user {user.id}: {e}` | Log (error) | `backend/open_webui/routers/auths.py:700` | LDAP group mapping failed; sign-in still succeeds | None | Group memberships may be stale: escalate |
| `LDAP Group Management enabled but {LDAP_ATTRIBUTE_FOR_GROUPS} attribute not found in user entry` | Log (warning) | `backend/open_webui/routers/auths.py:631-634` | Group Mapping is on but the directory entry lacks the **Group Attribute** | None | Explains "my LDAP groups do not appear" |
| `Signup error: {err}` | Log (error) | `backend/open_webui/routers/auths.py:951` | Behind `An internal error occurred during signup.` | None | Escalate |
| `Add user error: {err}` | Log (error) | `backend/open_webui/routers/auths.py:1162` | Behind `An internal error occurred while adding the user.` | None | Escalate |
| `OpenID signout error: {e}` | Log (error) | `backend/open_webui/routers/auths.py:1042` | Behind `Failed to sign out from the OpenID provider.` | None | See `sso-oauth-oidc-and-scim.md` |
| `Cannot revoke tokens for user {user_id}: Redis is not configured, existing sessions stay valid until expiry.` | Log (warning) | `backend/open_webui/utils/auth.py:353-358` | A password change or admin password reset on a server without Redis | None | Confirms other devices stayed signed in |
| `Unsupported PASSWORD_HASH_ALGORITHM: {PASSWORD_HASH_ALGORITHM}` | Error | `backend/open_webui/utils/auth.py:187` | The algorithm variable holds something other than `bcrypt` or `argon2`; new passwords cannot be saved (sign-up then shows `An internal error occurred during signup.`) | None | Escalate: server configuration |
| `Invalid PASSWORD_VALIDATION_REGEX_PATTERN: {e}` | Log (error, at start-up) | `backend/open_webui/env.py:822-827` | The operator's password pattern cannot be read; the default pattern is used instead | None | Escalate |
| `⚠️  SECURITY WARNING: JWT_EXPIRES_IN is set to '-1'` | Log (warning, at start-up) | `backend/open_webui/config.py:2468-2472` | `JWT_EXPIRES_IN=-1` in the environment | None | Policy question |
| `WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.` | Start-up stop (first line of a longer message) | `backend/open_webui/env.py:780-788` | The server was started without a secret key while authentication is on; it does not start | None | Escalate: deployment |
| `Failed to add user {user_id} to default group {default_group_id}: {e}` | Log (error) | `backend/open_webui/utils/groups.py:20-24` | The **Default Group** could not be applied to a new account (for example the group was deleted) | None | Ask an admin to check **Default Group** |
| `Creating admin account from environment variables: {email}` | Log (info, at start-up) | `backend/open_webui/utils/auth.py:648` | First-admin bootstrap ran | None | Contains an email address |
| `Failed to create admin account from environment variables` | Log (error, at start-up) | `backend/open_webui/utils/auth.py:661` | The bootstrap insert returned nothing | None | Escalate |
| `Error creating admin account: {e}` | Log (error, at start-up) | `backend/open_webui/utils/auth.py:663-664` | The bootstrap failed with an error | None | Escalate |
| `authenticate_user: {email}` | Log (info) | `backend/open_webui/models/auths.py:151` | Every email-and-password attempt, with the email as typed | None | The server log therefore holds sign-in emails: personal data |
| `Admin details - Email: {admin_email}, Name: {admin_name}` | Log (info) | `backend/open_webui/routers/auths.py:1179` | Each time a `pending` overlay asks for the admin contact | None | Personal data in the log |

## 11. Common Tier-1 Issues and Troubleshooting

Ground rules for every item below: tier 1 is read-only and never changes data, settings, roles or
access. Never ask for, or accept, a password, session token or API key; if a person pastes one
into a ticket, tell them to change or replace it and treat it as a possible security incident
(security.utoronto.ca). Email addresses in escalations are personal data: send them only through
the approved ticket channel (TO BE CONFIRMED). The escalation contact for the platform maintainer
is **TO BE CONFIRMED**.

### 11.1 "I can't sign in with my email and password"

**Symptom.** A red pop-up reads
`The email or password provided is incorrect. Please check for typos and try logging in again.`

**Likely causes, in order.**
1. A typo in the email or password, or Caps Lock (`backend/open_webui/routers/auths.py:824-833`).
2. The account was created through single sign-on, LDAP or SCIM, so it has no password the person
   knows; they should use the single sign-on button or LDAP form instead
   (`backend/open_webui/utils/oauth.py:2117-2125`; `backend/open_webui/routers/auths.py:652-658`;
   `backend/open_webui/models/auths.py:158-161`).
3. A different email address (old address, alias, or a typo in the account's stored email).
4. No account exists for that email (the server gives the same message;
   `backend/open_webui/models/auths.py:153-155`).
5. The credential was deactivated directly in the database (`auth.active`); the application itself
   never does this (`backend/open_webui/models/auths.py:120-125`, `:159-161`).

**Diagnostic steps.**
1. Ask how the person signed in last time (button, LDAP form or email form) and which email.
2. Ask them to use the eye button in the **Password** field to check what they typed
   (`src/lib/components/common/SensitiveInput.svelte:55-63`).
3. Ask an admin to look the person up in the admin user list (read-only) and confirm the exact
   email and role (`users-groups-roles-and-permissions.md`).
4. If they have tried many times, see 11.2 before they try again.

**Resolution.** Guidance only: correct email, careful retyping, or the right sign-in method. If the
password is forgotten, see 11.14.

**Escalation.** Send: the email address used (through the ticket channel), the sign-in method
expected, the exact message, the time and time zone of the last attempt, and whether the account
appears in the admin user list. Never include the password.

### 11.2 "It says 'API rate limit exceeded' when I sign in"

**Symptom.** A red pop-up reads `API rate limit exceeded` on the sign-in page.

**Likely causes, in order.**
1. More than 15 attempts for the same email within three to four minutes. Successful sign-ins
   count too, and every attempt made while refused adds to the count
   (`backend/open_webui/routers/auths.py:91`, `:818-828`; `backend/open_webui/utils/rate_limit.py:79-109`).
2. A password manager, browser extension or script retrying automatically.
3. Several people or devices signing in with the same email at once.
4. Without Redis, each server process counts separately, so the exact point of refusal can vary
   (`backend/open_webui/utils/rate_limit.py:55-61`).

**Diagnostic steps.** Ask how many attempts were made and over what time; ask whether anything
signs in automatically with that email.

**Resolution.** Ask the person to stop all attempts (including automated ones) for at least four
minutes, then try once, carefully. There is no account lockout to clear and no admin action that
resets the counter.

**Escalation.** If the refusal continues after ten quiet minutes, send the email address, the
times of the attempts and whether any automation uses the account.

### 11.3 "I made an account but all I see is 'Account Activation Pending'"

**Symptom.** After signing up (or signing in for the first time through LDAP), a full-screen panel
shows `Account Activation Pending` / `Contact Admin for WebUI Access` (or the organization's custom
text) with **Check Again** and **Sign Out**.

**Likely causes, in order.**
1. New accounts get the default role `pending` (code default) and wait for an admin
   (`backend/open_webui/config.py:1720`; `backend/open_webui/routers/auths.py:868`).
2. The admin has approved the person but the page has not been reloaded (section 5.5, step 5).

**Diagnostic steps.**
1. Ask the person to press **Check Again** (or reload).
2. Ask an admin whether the account still shows `pending` in the admin user list.

**Resolution.** Explain that an admin must approve the account; no email arrives when that happens
(section 9). After approval, **Check Again** opens the app. If the overlay was left open until the
session expired, the code path shows `Session expired. Please sign in again.` and then an empty
page, because the app shell only redirects people whose app has finished loading; reloading the
page leads to the sign-in page (`src/routes/(app)/+layout.svelte:213-220`, `:411-413`, `:440`).

**Escalation.** Send the email address and the date of sign-up to whoever approves accounts (the
approval route is **TO BE CONFIRMED**).

### 11.4 "There's no 'Sign up' link" or "Sign-up says I don't have permission"

**Symptom.** The sign-in page has no `Don't have an account?` link, or sign-up fails with
`You do not have permission to access this resource. Please contact your administrator for assistance.`

**Likely causes, in order.**
1. **New Sign Ups** is off. It switches off automatically when the first admin is created
   (`backend/open_webui/routers/auths.py:874-879`; `backend/open_webui/main.py:376-380`).
2. **Login Form** is off, which also blocks sign-up (`backend/open_webui/routers/auths.py:908-911`).
3. The page is in LDAP mode, which never shows the sign-up link (`src/routes/auth/+page.svelte:390-446`).
4. The deployment provides accounts through single sign-on instead (OAuth sign-up has its own
   switch; `sso-oauth-oidc-and-scim.md`).

**Diagnostic steps.** Note which buttons and fields the sign-in page shows (a screenshot without
any typed password is ideal).

**Resolution.** Explain how accounts are obtained in this deployment (**TO BE CONFIRMED**: self
sign-up, single sign-on, or admin-created accounts).

**Escalation.** Account requests go to whoever creates accounts (**TO BE CONFIRMED**).

### 11.5 "The sign-in page has no email and password boxes"

**Symptom.** `/auth` shows only `Continue with …` buttons, or only the title with nothing to click.

**Likely causes, in order.**
1. The admin hid the login form (**Login Form** off), intending single sign-on only
   (`src/routes/auth/+page.svelte:296`, `:389`).
2. Both the login form and LDAP are off and no single sign-on provider is offered (OAuth off, or no
   provider registered), so the page has nothing to offer (`backend/open_webui/main.py:2317-2324`;
   `src/routes/auth/+page.svelte:451`).
3. The page has just forwarded, or is about to forward, to the single sign-on provider because
   **Auto Redirect** is on (`src/routes/auth/+page.svelte:180-195`).

**Diagnostic steps.** Ask for a screenshot; ask whether a **Continue with …** button is present and
what happens when it is pressed.

**Resolution.** If buttons are shown, guide the person to the single sign-on button. If nothing is
shown, nobody can sign in through the page.

**Escalation.** "Nothing to sign in with" is a service-level problem: escalate immediately with the
time and a screenshot.

### 11.6 "LDAP sign-in says 'LDAP authentication failed.'"

**Symptom.** The LDAP form (**Username**, **Password**, **Authenticate**) answers
`LDAP authentication failed.`

**Likely causes, in order.**
1. Wrong directory password (`Authentication failed.` in the log;
   `backend/open_webui/routers/auths.py:644-645`).
2. The username is not in the form the directory expects (for example `jdoe` versus
   `jdoe@example.com`), so no entry is found (`User not found in the LDAP server`;
   `backend/open_webui/routers/auths.py:558-565`).
3. A **Search Filters** value copied from the placeholder example containing `%s`, which makes
   every search fail (section 7.3).
4. The directory entry has no email (`User does not have a valid email address.`;
   `backend/open_webui/routers/auths.py:578-579`).
5. The application account (**Application DN**) can no longer bind, so it fails for everyone
   (`Application account bind failed`; `backend/open_webui/routers/auths.py:541-542`).
6. An existing MedIT GPT account with the same email has no active local credential (for example
   an account created by SCIM) (`backend/open_webui/routers/auths.py:690-704`).

**Diagnostic steps.**
1. Ask whether the same username and password work for other services that use the directory.
2. Ask whether colleagues can sign in with LDAP right now; if nobody can, causes 3 or 5 are likely.
3. Record the exact time of a failed attempt so the maintainer can find the log line
   `LDAP authentication error: {e}` (section 10.3).

**Resolution.** Guidance on the username format and directory password only.

**Escalation.** Send the username format used (not the password), the time of the attempt, and
whether other people are affected.

### 11.7 "I keep getting 'Session expired. Please sign in again.'"

**Symptom.** The pop-up `Session expired. Please sign in again.` appears and the sign-in page opens,
more often than expected.

**Likely causes, in order.**
1. The session simply reached **JWT Expiration** (code default four weeks), counted from sign-in,
   not from last activity (sections 4 and 5.8).
2. A short **JWT Expiration** set by an admin (for example `30m`) (`backend/open_webui/config.py:2466`).
3. The password was changed or reset elsewhere, which revokes every session when Redis is
   configured (`backend/open_webui/routers/auths.py:408-411`; `backend/open_webui/routers/users.py:968-970`).
4. The server's secret key changed (for example a redeploy without a persistent key), which ends
   every session at once (ground truth; 11.9).
5. The computer's clock is far ahead: the browser compares the token's expiry with the local clock
   (`src/routes/+layout.svelte:965-977`).
6. Clearing the browser's data for the site removes the stored token and cookie (section 6.5).

**Diagnostic steps.**
1. Ask how long after signing in it happens, and whether other people see it at the same time.
2. Ask whether the person (or an admin) recently changed the password.
3. Ask an admin for the current **JWT Expiration** value (read-only).
4. Ask whether the computer's date and time are correct.

**Resolution.** Explain the session length; suggest correcting the computer clock; suggest not
clearing site data for MedIT GPT. After signing in again the person returns to the page they were
on.

**Escalation.** If many people are affected at once, escalate immediately (likely 11.9). Otherwise
send the observed interval and the **JWT Expiration** value.

### 11.8 "I see '401 Unauthorized' when I open MedIT GPT"

**Symptom.** On opening or reloading the site, red pop-ups read `Session expired. Please sign in again.`
and `401 Unauthorized` (or `Invalid token`, or
`Your session has expired or the token is invalid. Please sign in again.`), then the sign-in page
appears.

**Likely causes, in order.** The second pop-up identifies the cause (table in section 5.8):
1. `401 Unauthorized`: the stored token expired while the site was closed, or the server's secret
   key changed (`backend/open_webui/utils/auth.py:489-493`).
2. `Invalid token`: the session was revoked, usually by a password change or reset (Redis only)
   (`backend/open_webui/utils/auth.py:449-453`).
3. `Your session has expired or the token is invalid. Please sign in again.`: the account was
   deleted (`backend/open_webui/utils/auth.py:455-460`).

**Diagnostic steps.** Ask for the exact text of the second pop-up and whether signing in again
works.

**Resolution.** Ask the person to sign in again. This is expected behaviour, not a fault, unless
it happens to many people at once or immediately after each sign-in.

**Escalation.** If signing in works but the message returns immediately, or many people are
affected, escalate with the times and the exact texts. If the third text appears, the account
itself may be gone: escalate to an admin.

### 11.9 "Everyone was signed out at the same time"

**Symptom.** Many people report `Session expired. Please sign in again.` and `401 Unauthorized` at
about the same time, usually just after maintenance.

**Likely causes, in order.**
1. The server's `WEBUI_SECRET_KEY` changed, for example a container was recreated without a
   persistent key; every existing token becomes unreadable (ground truth; `backend/open_webui/utils/auth.py:246-251`).
2. The site moved to a different address: the browser keeps the token per site address
   (section 6.5), so people must sign in again at the new one.
3. Tokens issued with a very short **JWT Expiration** all reached their end (section 5.8).

**Diagnostic steps.** Establish the start time, whether a deployment or restart happened, and the
exact second pop-up text (section 5.8).

**Resolution.** Ask people to sign in again; their accounts and chats are unaffected by a key
change.

**Escalation.** Escalate immediately to the platform maintainer with the start time and the number
of people affected. A secret-key change also makes encrypted tool settings and stored single
sign-on data unreadable (ground truth), which the maintainer must assess.

### 11.10 "I signed out, but I'm still signed in on my other computer"

**Symptom.** After **Sign Out** on one device, MedIT GPT still works on another browser or device.

**Likely causes, in order.**
1. Sign-out ends only the session of the browser that signed out; each device has its own token
   (`backend/open_webui/utils/auth.py:315-340`).
2. Without Redis, even the signed-out token is not revoked on the server
   (`backend/open_webui/utils/auth.py:322-323`).

**Diagnostic steps.** Ask which devices are still signed in and whether any device is lost or
shared.

**Resolution.** Sign out on each device. Changing the password ends every session at once, but only
when Redis is configured (section 5.11); whether production has Redis is TO BE CONFIRMED. A lost or
stolen device that is still signed in is a possible security incident: refer to U of T Information
Security (security.utoronto.ca) and the platform maintainer.

**Escalation.** Send the account email, the devices involved and when the person signed out.

### 11.11 "My new password is rejected"

**Symptom.** Sign-up, **Change Password** or an admin's **Add User** refuses the new password.

**Likely causes, in order.**
1. Over 72 bytes with the `bcrypt` algorithm:
   `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.`
   Accented letters and emoji use more than one byte each (section 5.10).
2. The optional pattern is on: `The password does not meet the required validation criteria.`, or
   the operator's hint text (`backend/open_webui/utils/auth.py:197-199`).
3. The two new entries differ:
   `The passwords you entered don't quite match. Please double-check and try again.` or, at sign-up,
   `Passwords do not match.`

**Diagnostic steps.** Get the exact message (never the password).

**Resolution.** Guide the person: a shorter password without many accented letters or emoji for
cause 1; a longer password mixing upper- and lower-case letters, digits and a symbol for cause 2
(the actual rule is TO BE CONFIRMED); retype both entries for cause 3.

**Escalation.** If the generic pattern message appears and the person cannot find a passing
password, ask the platform maintainer to publish the rule or set a hint.

### 11.12 "Change Password says my current password is incorrect"

**Symptom.** **Update password** answers
`The password provided is incorrect. Please check for typos and try again.`

**Likely causes, in order.**
1. The account signs in through single sign-on or LDAP, so it has no local password the person
   knows (`backend/open_webui/utils/oauth.py:2117-2125`; `backend/open_webui/routers/auths.py:652-658`).
2. A typo in **Current Password**.

**Diagnostic steps.** Ask how the person signs in.

**Resolution.** Single sign-on and LDAP users change their password with the identity provider or
directory (U of T process **TO BE CONFIRMED**); everyone else retypes carefully.

**Escalation.** None normally; if an email-and-password user is sure of the current password,
escalate with the time of the attempt.

### 11.13 "I can't find where to change my password"

**Symptom.** **Settings → Account** has no **Password** section.

**Likely causes, in order.**
1. The admin hid the login form (single sign-on deployment); the section is hidden with it
   (`src/lib/components/chat/Settings/Account.svelte:381`).
2. The password-change form is switched off through `ENABLE_PASSWORD_CHANGE_FORM`
   (`backend/open_webui/config.py:1668`; `backend/open_webui/main.py:2346`).
3. The person is `pending` and cannot open Settings at all (section 5.5).

**Diagnostic steps.** Ask whether the person signs in with a single sign-on button.

**Resolution.** Explain that passwords for single sign-on accounts are changed with the identity
provider (TO BE CONFIRMED). If the person uses email and password and the section is missing,
escalate.

**Escalation.** Send the account email and the sign-in method.

### 11.14 "I forgot my password"

**Symptom.** The person cannot remember the password for the email form.

**Likely causes, in order.** Not applicable.

**Diagnostic steps.** Confirm the person really uses the email form (not single sign-on or LDAP).

**Resolution.** There is no self-service reset and no reset email (section 5.11). An admin can set
a new password in the admin user editor (`backend/open_webui/routers/users.py:962-970`), which also
ends the person's other sessions when Redis is configured. Single sign-on and LDAP passwords are
reset through the identity provider. Tier 1 does not reset passwords.

**Escalation.** Send the account email to an admin through the approved route; the identity
verification required before an admin sets a password is **TO BE CONFIRMED**.

### 11.15 "I can't find API keys in my settings"

**Symptom.** **Settings → Account** has no **API keys** section.

**Likely causes, in order.**
1. The global **API Keys** switch is off (code default) (`backend/open_webui/config.py:2454`).
2. The person is not an admin and does not hold `features.api_keys` (code default off) through the
   defaults or a group (`backend/open_webui/config.py:1924`; `src/lib/utils/settings-access.ts:13-15`).
3. The section is present but collapsed: the key appears only after pressing **Show** on the
   **Secrets** row (`src/lib/components/chat/Settings/Account.svelte:389-400`).

**Diagnostic steps.** Ask whether a **Secrets** row with **Show** is visible.

**Resolution.** For cause 3, guide the person to **Show**. Otherwise explain that API keys must be
enabled for them; the policy on who may have keys is **TO BE CONFIRMED**.

**Escalation.** Requests for API access go to an admin with the account email and the purpose.

### 11.16 "Clicking 'Create new secret key' does nothing"

**Symptom.** Pressing **Create new secret key** (or **Create new key**) shows no pop-up and no key.

**Likely causes, in order.**
1. The server refused (for example the switch or the permission was removed after the tab was
   opened); the button's code shows no error (`src/lib/components/chat/Settings/Account.svelte:181-188`;
   `backend/open_webui/routers/auths.py:1517-1525`).
2. A network problem between the browser and the server.

**Diagnostic steps.** Ask the person to close and reopen **Settings → Account**. If the **API keys**
section has disappeared, access was removed (11.15).

**Resolution.** Reopen the tab and try once more.

**Escalation.** If the section is still shown and nothing happens, send the account email, the time
and the browser used.

### 11.17 "My API key returns 'Use of API key is not enabled in the environment.'"

**Symptom.** A program using the key gets HTTP 403 with
`Use of API key is not enabled in the environment.`

**Likely causes, in order.**
1. An admin switched the global **API Keys** setting off (`backend/open_webui/utils/auth.py:526-527`).
2. The owner lost `features.api_keys` (for example removed from a group) and is not an admin
   (`backend/open_webui/utils/auth.py:529-536`).

**Diagnostic steps.** Ask whether the **API keys** section still appears in the owner's
**Settings → Account**.

**Resolution.** Explain that access was withdrawn; the key itself still exists and would work again
if access were restored. Tier 1 cannot restore access.

**Escalation.** Send the account email and the program's purpose to an admin.

### 11.18 "My API key works for some things but others say I don't have permission"

**Symptom.** Some calls with the key succeed; others answer
`You do not have permission to access this resource. Please contact your administrator for assistance.`

**Likely causes, in order.**
1. **API Key Endpoint Restrictions** is on and the path is not under **Allowed Endpoints** (HTTP 403)
   (`backend/open_webui/utils/auth.py:538-550`).
2. The path is for admins only, or the key's owner is `pending` (HTTP 401)
   (`backend/open_webui/utils/auth.py:567-576`, `:625-631`).
3. The feature behind that path needs another permission (documented in the feature's own area).

**Diagnostic steps.** Record the failing path and the HTTP status (403 or 401); ask an admin for the
**Allowed Endpoints** list (read-only).

**Resolution.** Explain which calls the key may make. Tier 1 cannot change the list.

**Escalation.** Send the path, status and account email to an admin.

### 11.19 "Nothing happens when I click Sign in"

**Symptom.** The button shows a spinner briefly, then the page stays as it was with no pop-up.

**Likely causes, in order.**
1. The browser could not reach the server, or something between them (a proxy, firewall or captive
   portal) answered with a page that is not the application's; the sign-in helper then ends without
   an error text (`src/lib/apis/auths/index.ts:326-341`; `src/routes/auth/+page.svelte:47-48`,
   `:73-80`).
2. A browser extension blocking requests to the site.

**Diagnostic steps.** Ask whether other pages of the site load, whether the person is on the
expected network or VPN (requirement TO BE CONFIRMED), and whether another browser behaves the
same. People comfortable with developer tools can read the error in the browser console.

**Resolution.** Try another network or browser; disable blocking extensions for the site.

**Escalation.** If several people are affected, escalate as a possible outage with times and
networks.

### 11.20 "Nothing happens when I click Sign Out"

**Symptom.** **Sign Out** in the user menu does not leave the app.

**Likely causes, in order.**
1. Single sign-on sign-out failed on the server (`Failed to sign out from the OpenID provider.`) and
   the menu has no error handling, so the browser keeps its token
   (`src/lib/components/layout/Sidebar/UserMenu.svelte:582-587`;
   `backend/open_webui/routers/auths.py:1041-1047`).

**Diagnostic steps.** Ask whether the person signs in with single sign-on, and whether the next
action in the app then shows `Session expired. Please sign in again.` (the server may already have
revoked the token when Redis is configured, `backend/open_webui/routers/auths.py:970-975`).

**Resolution.** Try again later. On a shared computer, clearing the browser's data for the site
removes the stored token (section 6.5).

**Escalation.** Send the time and sign-in method; see `sso-oauth-oidc-and-scim.md`.

### 11.21 "The page says 'MedIT GPT Backend Required'"

**Symptom.** Instead of the sign-in page, the site shows `{{webUIName}} Backend Required` (displayed
as "MedIT GPT Backend Required") and
`Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.`
with a **Check Again** button.

**Likely causes, in order.**
1. The application server is down or restarting, so `/api/config` could not be read
   (`src/routes/+layout.svelte:1238-1250`, `:1315-1317`).
2. A network or proxy problem between the person and the server.

**Diagnostic steps.** Ask whether colleagues see the same; note the time.

**Resolution.** Press **Check Again** after a few minutes. The links on that page go to the upstream
Open WebUI project, not MedIT GPT support (`src/routes/error/+page.svelte:35-43`).

**Escalation.** Escalate immediately as a possible outage with the time and number of people
affected.

### 11.22 "I changed the JWT Expiration but nothing changed" (admins)

**Symptom.** After saving a new **JWT Expiration**, sessions still last as before, or the stored
value differs from what was typed.

**Likely causes, in order.**
1. Existing sessions keep the expiry they were issued with; only new sign-ins use the new value
   (`backend/open_webui/routers/auths.py:186-194`).
2. The value was not one the server accepts (for example `1h30m` or `2 days`); it is ignored
   silently while the panel still says `Settings saved successfully!`
   (`backend/open_webui/routers/auths.py:1289-1293`; `src/lib/components/admin/Settings/Authentication.svelte:89-107`).

**Diagnostic steps.** Ask the admin to close and reopen the **Authentication** tab and read the
stored value.

**Resolution.** Accepted forms are `-1`, `0`, or one number with one unit `ms`, `s`, `m`, `h`, `d`
or `w` (for example `12h`). Existing sessions end at their original time unless people sign in again.

**Escalation.** Not normally needed.

### 11.23 "The pending screen shows the wrong admin contact, or none"

**Symptom.** The `Admin: …` line on the pending overlay is missing, shows an unexpected person, or
shows only an email in brackets.

**Likely causes, in order.**
1. **Admin Details** is off, so no line is shown (`backend/open_webui/routers/auths.py:1195-1196`).
2. **Admin Contact Email** is empty, so the earliest-created account is shown, whatever its role now
   (`backend/open_webui/routers/auths.py:1185-1189`; `backend/open_webui/models/users.py:715-720`).
3. **Admin Contact Email** names an address that has no account, so the name is blank
   (`backend/open_webui/routers/auths.py:1181-1184`).

**Diagnostic steps.** Get a screenshot from the person (it contains an admin's name and email:
handle as personal data).

**Resolution.** Report the problem to an admin; tier 1 does not change the setting.

**Escalation.** Send the screenshot through the ticket channel.

### 11.24 "Single sign-on says the email or password is incorrect"

**Symptom.** After choosing a **Continue with …** button the sign-in page shows
`The email or password provided is incorrect. Please check for typos and try logging in again.`
although no password was typed.

**Likely causes, in order.** Single sign-on failures such as a blocked email domain reuse this
message (ground truth). The full list is in `sso-oauth-oidc-and-scim.md`.

**Diagnostic steps.** Note the provider button used and the time.

**Resolution.** Follow `sso-oauth-oidc-and-scim.md`.

**Escalation.** As described there.

### 11.25 "I think my API key or session token was exposed"

**Symptom.** A person reports that their API key or token was pasted somewhere public, shared, or
included in a ticket.

**Likely causes, in order.** Not applicable.

**Diagnostic steps.** Do not ask for, copy or repeat the key or token. Record only where and when it
was exposed.

**Resolution.** Treat it as a suspected security incident and refer it to U of T Information
Security (security.utoronto.ca) and the platform maintainer. The person can replace or delete
their own key in **Settings → Account** (section 5.12); the old key stops working immediately.
Changing the password ends existing sessions only when Redis is configured (section 5.11).

**Escalation.** Report to security.utoronto.ca and the platform maintainer with the account email,
what was exposed (key or token, not its value), where and when.

## 12. Local Customisations

Compared with upstream Open WebUI v0.11.4 (`git diff main...uoft`), the authentication logic in
this area is unchanged: `backend/open_webui/routers/auths.py`, `backend/open_webui/utils/auth.py`,
`backend/open_webui/models/auths.py`, `backend/open_webui/utils/rate_limit.py`,
`backend/open_webui/utils/validate.py`, `backend/open_webui/constants.py`,
`backend/open_webui/main.py`, `src/routes/auth/+page.svelte`, `src/routes/(app)/+layout.svelte`,
`src/lib/apis/auths/index.ts`, `src/lib/components/layout/Overlay/AccountPending.svelte`,
`src/lib/components/chat/Settings/Account.svelte`, `src/lib/components/chat/Settings/Account/` and
`src/lib/components/admin/Settings/Authentication.svelte` have no fork changes and no uncommitted
changes.

What the fork changes that people see in this area:

| Change | Where it shows | Source |
|---|---|---|
| Default product name `MedIT GPT`, and the upstream habit of appending ` (Open WebUI)` to a custom name removed | Every sign-in title ("Sign in to MedIT GPT", "Get started with MedIT GPT", "Signing in to MedIT GPT"), the browser tab, the first-run note | `backend/open_webui/env.py:951`; `src/lib/constants.ts:7` |
| The first-run welcome screen shows the product name instead of the fixed words "Open WebUI" | First run only | `src/lib/components/OnBoarding.svelte:3`, `:78-80` |
| U of T logo files replace the upstream ones | The logo on `/auth` and the welcome screen (`/static/favicon.png`) | `backend/open_webui/static/favicon.png`; `static/static/favicon.png`; `static/favicon.png`; served by `backend/open_webui/main.py:3023` |

`WEBUI_NAME` is an environment variable, so the live product name is **TO BE CONFIRMED** (ground
truth). Fork changes elsewhere in the touched files (`src/routes/+layout.svelte:622`, `:760`, `:873`
browser-notification titles; `backend/open_webui/models/users.py:99-100` two interface settings) do
not concern authentication.

**Uncommitted working-tree change with an indirect effect.** `src/lib/i18n/index.ts` now maps the
browser's language to a bundled language more carefully and adds English as a final fallback when
an admin sets a default language (`src/lib/i18n/index.ts:75-86`, `:93`, `:105`). This changes which
translation of the sign-in, overlay and Account texts a person sees, not what the code does. The
only uncommitted change to `src/lib/i18n/locales/en-US/translation.json` concerns a non-auth
setting (Hide Processing Details).

## 13. Source File Index

"Full" means the file was read from start to end; "parts" lists what was read.

| File | What it holds for this area | Read |
|---|---|---|
| `backend/open_webui/routers/auths.py` | Every `/api/v1/auths` endpoint: session check, profile, time zone, password change, LDAP, sign-in, sign-up, sign-out, admin config, LDAP config, OAuth config, API keys, token exchange, rate limiter | Full |
| `backend/open_webui/utils/auth.py` | Password rules and checking, token creation and reading, revocation, API-key resolution, role checks, first-admin bootstrap | Full |
| `backend/open_webui/models/auths.py` | `auth` table, sign-in, sign-up and password forms, account creation and credential checks | Full |
| `backend/open_webui/models/users.py` | `user` and `api_key` tables, email and key lookups, first user, API-key create and delete | Parts: 138-928 |
| `backend/open_webui/utils/rate_limit.py` | Sliding-window rate limiter (Redis or memory) | Full |
| `backend/open_webui/utils/validate.py` | Profile-picture and background-image validation | Full |
| `backend/open_webui/constants.py` | `ERROR_MESSAGES` texts | Full |
| `backend/open_webui/main.py` | `/api/config`, router mount, first-admin bootstrap at start-up, session middleware, static mount | Parts: 360-392, 856, 2224-2472, 2640-2674, 3023 |
| `backend/open_webui/env.py` | `WEBUI_AUTH`, secret key, cookie flags, admin bootstrap, trusted headers, password settings, sign-out redirect, product name | Parts: 362-364, 384, 745-830, 860-868, 951, 965-985 |
| `backend/open_webui/config.py` | Sign-up, login-form, password-change, password-auth switches; default role and group; overlay text; API-key and JWT settings; LDAP settings; `DEFAULT_CONFIG` keys | Parts: 1655-1730, 1924, 1995-2012, 2160-2175, 2450-2490, 2788-2820, 3080-3160, 3211-3227 |
| `backend/open_webui/events.py` | Auth event definitions, sinks, webhook message format, payload fields | Parts: 80-150, 669-704, 854-878, 947-1202 |
| `backend/open_webui/socket/main.py` | Disconnecting an account's live connections; live-connection sign-in | Parts: 388-452 |
| `backend/open_webui/utils/groups.py` | Default-group assignment | Parts: 8-24 |
| `backend/open_webui/utils/misc.py` | `parse_duration`, `validate_email_format`, `throttle` | Parts: 869-874, 1012-1041, 1158-1183 |
| `backend/open_webui/utils/asgi_middleware.py` | Where API keys and cookies are picked up from a request | Parts: 90-180 |
| `backend/open_webui/routers/users.py` | Admin setting a user's password | Parts: 940-985 |
| `backend/open_webui/utils/oauth.py` | How single sign-on accounts are created (password nobody knows) | Parts: 2110-2125 |
| `src/routes/auth/+page.svelte` | The sign-in page | Full |
| `src/lib/apis/auths/index.ts` | Browser helpers for every auth endpoint; sign-out redirect logic | Full |
| `src/lib/components/layout/Overlay/AccountPending.svelte` | Account Activation Pending overlay | Full |
| `src/lib/components/chat/Settings/Account.svelte` | Settings → Account (profile, user variables, password section, API keys, JWT) | Full |
| `src/lib/components/chat/Settings/Account/UpdatePassword.svelte` | Change Password form | Full |
| `src/lib/components/chat/Settings/Account/UserProfileImage.svelte` | Profile picture buttons | Full |
| `src/lib/components/admin/Settings/Authentication.svelte` | Admin Authentication tab | Full |
| `src/routes/+layout.svelte` | Session bootstrap, request watcher, expiry timer, live connection | Parts: 1-320, 890-1452 |
| `src/routes/(app)/+layout.svelte` | Redirect to `/auth`, pending overlay, app loading | Full |
| `src/routes/error/+page.svelte` | "Backend Required" page | Full |
| `src/routes/(app)/admin/+page.svelte`, `src/routes/(app)/admin/settings/+page.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Admin deep links into the Settings window | Full |
| `src/lib/components/OnBoarding.svelte` | First-run welcome screen | Parts: 1-7 (via diff), 40-126 |
| `src/lib/components/common/SensitiveInput.svelte` | Password fields and the show-password button | Full |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | **Settings**, **Admin Panel** and **Sign Out** menu items | Parts: 565-598, plus a search of every label and `admin` reference in the file |
| `src/lib/components/chat/SettingsModal.svelte` | Tab list, groups, Account save toast, admin tabs | Parts: 95-180, 245-282, 495-515, 714-860 |
| `src/lib/utils/settings-access.ts` | `canUseApiKeys` and settings search rules | Parts: 10-69 |
| `src/lib/apis/index.ts` | `getBackendConfig` and the single sign-on proxy probe | Parts: 1469-1520 |
| `src/lib/i18n/index.ts`, `src/lib/i18n/settings-translations.ts` | Translation loading, fallbacks and admin overrides | Full |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted settings keys | Parts: keys `settings.personal.account.*` (2743-2767), `settings.admin.authentication.*` (2022-2136) and the plain keys quoted |
| `src/lib/utils/index.ts` | Initials avatar, browser time zone | Parts: 454-484, 1414-1416 |
| `src/lib/constants.ts` | `APP_NAME`, base URLs | Parts: 1-30 |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Where tool-server OAuth sessions are disconnected | Parts: 595-630 |
| `.venv/lib/python3.12/site-packages/starlette/exceptions.py` (local environment, not repository code) | How an `HTTPException` prints in the LDAP log line | Parts: 7-19 |

## 14. Open Questions

Everything below could not be established from the repository. Items 1 to 9 are configuration or
organizational facts held outside the code; items 10 to 14 are behaviours read from the code but
not exercised; item 15 lists security-sensitive matters deliberately left undescribed.

1. **Which sign-in methods production offers.** Values of `WEBUI_AUTH`, `ENABLE_PASSWORD_AUTH`,
   `ui.enable_login_form`, `ldap.enable`, `oauth.enable`, the registered OAuth providers and
   trusted-header variables. These decide what `/auth` shows (section 5.1). Data and environment:
   TO BE CONFIRMED.
2. **Live values of every setting in section 7**: `ui.default_user_role`, `ui.default_group_id`,
   `ui.enable_signup`, `ui.enable_password_change_form`, the pending-overlay title and content,
   `auth.admin.show`, `auth.admin.email`, `auth.jwt_expiry`, `auth.enable_api_keys`, the endpoint
   restrictions and allowed endpoints, the `features.api_keys` default and which groups grant it,
   all `ldap.*` keys, and any `ui.i18n` wording overrides.
3. **Whether Redis is configured** and how many server processes run. This decides whether sign-out
   and password changes end sessions on the server and whether the sign-in rate limit is shared
   (sections 5.9, 5.11, 4).
4. **Password policy in force**: `PASSWORD_HASH_ALGORITHM`, `ENABLE_PASSWORD_VALIDATION`, the
   pattern and the hint. Needed to answer "what are the password rules?" (section 5.10).
5. **Cookie and sign-out settings**: `WEBUI_AUTH_COOKIE_SECURE`, `WEBUI_AUTH_COOKIE_SAME_SITE`,
   `WEBUI_SESSION_COOKIE_*`, `WEBUI_AUTH_SIGNOUT_REDIRECT_URL`, `ENABLE_STAR_SESSIONS_MIDDLEWARE`.
6. **How people obtain accounts** (self sign-up, single sign-on with UTORid, LDAP, or admin-created),
   who approves `pending` accounts, through which channel, and how fast. The repository has no
   contact, queue or service level (ground truth).
7. **U of T processes** for changing or resetting passwords of single sign-on and LDAP accounts, and
   the identity checks an admin must make before setting a password for someone (sections 11.12,
   11.14).
8. **API-key policy**: who may hold keys, for what purposes, and whether endpoint restrictions are
   used (sections 5.12, 11.15).
9. **Network requirements**: whether MedIT GPT is reachable only on certain networks or through a
   VPN or proxy, and what LDAP username format is expected if LDAP is used (sections 11.6, 11.19).
10. **Behaviours traced by reading, not by running the application** (the instructions forbid
    starting it): the two pop-ups on reload with a refused token (section 5.8); the silent failure
    of **Create new secret key** on a refusal (section 5.12); the silent failure of **Sign in** on a
    network error (section 5.2); the silent failure of **Sign Out** when the server's sign-out
    errors (section 5.9); the empty page for a `pending` account whose session expires (section
    11.3); validation errors printed as the words [object Object]; the LDAP **Search Filters** `%s`
    pitfall (section 7.3). Each should be confirmed in a test environment.
11. **First-admin creation and sign-up.** The ground truth says sign-up is switched off once the
    first account exists. That is true for self-service sign-up, trusted-header sign-up and the
    environment bootstrap, but the LDAP path makes the first LDAP account an admin without
    switching **New Sign Ups** off (`backend/open_webui/routers/auths.py:663-667` versus
    `:874-879`). This refines rather than contradicts the ground truth; recorded for the
    maintainer.
12. **Rate-limit window.** The ground truth says 15 attempts per 180 seconds. The limiter counts in
    one-minute buckets and includes the current minute, so the effective window is between three
    and four minutes (`backend/open_webui/utils/rate_limit.py:30`, `:83-93`). A refinement, not a
    contradiction.
13. **Upstream wording that may not suit this deployment**: the first-run note says the product
    "does not make any external connections", the pending overlay says "WebUI", the error page
    describes a developer setup and links to the upstream GitHub and Discord, and the
    **Allowed Endpoints** and **JWT Expiration** links go to the upstream documentation
    (`src/routes/auth/+page.svelte:286-293`;
    `src/lib/components/layout/Overlay/AccountPending.svelte:34-50`;
    `src/routes/error/+page.svelte:28-43`;
    `src/lib/components/admin/Settings/Authentication.svelte:221-227`, `:243-251`). Whether to
    override this wording (section 7.6) is TO BE CONFIRMED.
14. **Tooling note.** `knowledgebase/tools/check_sections.py` accepts the glance heading only when
    spelled with a lower-case "glance" or with every word capitalized ("A Glance"); the research
    instructions prescribe the Title Case spelling "At a Glance", which this document uses, so the
    checker reports a false "no 'At a glance'" flag for it
    (`knowledgebase/tools/check_sections.py:37-38`). *Resolved 2026-10-07: the checker now matches
    the heading case-insensitively; recorded in `../tools/VERIFICATION.md`.*
15. **Security-sensitive: refer to the platform maintainer and U of T Information Security
    (security.utoronto.ca).** The following were reviewed and deliberately not described:
    how passwords, API keys and other credentials are stored; how token revocation behaves when
    the shared store is unavailable; how the hidden login form and the server-side password switch
    interact with each sign-in and sign-up path; which sign-in paths are subject to throttling
    beyond the email-and-password limit; and how locally stored credentials are set for accounts
    created through LDAP. None of these is needed for tier-1 diagnosis.
