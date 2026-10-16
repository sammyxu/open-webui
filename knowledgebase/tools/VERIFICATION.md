# Verification Report

What was checked against the source code, how, and what it found. **In progress:** Phase 2 is
under way (8 of 47 reference documents complete); the full Phase 4 sequence has not yet run. This
file records the checks and findings so far so nothing is lost between sessions.

**Verified so far:** 2026-10-07 and 2026-10-08 · **Against:** Open WebUI v0.11.4, branch `uoft`,
commit `aeed1832c` plus the uncommitted working-tree changes of 2026-10-07

## Summary

Eight reference documents (about 16,300 lines, 1,064 section-10 message rows) pass the section,
citation, link and personal-data checks. Of 1,032 quoted-message claims checked on 2026-10-08,
1,025 match the source and the 7 others are documented benign cases (below). One reference-layer defect was found and corrected (background-task
failure behaviour in the pipeline document); several ground-truth facts were refined from the
reference research, each re-verified in the main loop.

| Check | Scope | Result |
|---|---|---|
| Reference sections complete (`check_sections.py`) | 8 documents | 8 of 8 complete |
| Path and line citations (`validate.py`) | the 8 documents, ground truth, notes | all resolve; no line past end of file |
| Links and anchors (`check_links.py`) | whole knowledgebase | clean |
| Quoted messages exist (`verify_quotes.py`) | calibrated on `authentication-and-sign-in.md` (167 claims, 0 missing), then the other documents | residual flags all benign (below) |
| Personal-data grep (`pii_grep.py`) | all `.md`, `.json`, `.txt` | 0 hits |
| Scope coverage, structural facts, absolute-claim audit, transfer gap | | not yet run (Phase 4) |

## Defects Found and Fixed

### 1. Background-Task Failures Described as Always Swallowed

`chat-completion-pipeline-and-generation-tasks.md` (reference layer) said background-task failures
never reach the user and that a failed title falls back to the first message. The code shows that
title, tag and follow-up endpoints raise before their own error handling when the model is not in
the model list or a Pipelines inlet filter fails (`backend/open_webui/routers/tasks.py:157-167`,
`:197-200`); on the streaming path the exception reaches the chat handler and an error box appears
under a complete answer; on the non-streaming path it publishes `chat.failed`
(`backend/open_webui/utils/middleware.py:4388-4407`); the fallback title applies only while the
chat holds its first exchange (`backend/open_webui/utils/middleware.py:3990`). The original
researcher found this as its session ended; a correction agent applied it with evidence verified in
the main loop.

### 2. Ground-Truth Refinements From the Reference Research

Each was re-read against the source before `ground-truth.md` was edited (additive refinements,
marked *Refined* there): the LDAP path makes the first account an admin without switching sign-up
off; the sign-in limiter refuses the 16th attempt within three to four minutes and counts
successes; admins are subject to model access control when `BYPASS_ADMIN_ACCESS_CONTROL` is off;
group sync changes nothing on an empty claim and exempts blocked groups (which block nobody from
signing in); OAuth edits while not persisted live in one process's memory; the password message
also appears when the provider returns no user details.

### 3. Model Selector Location (Reference Layer)

`workspace-models-and-model-access.md` sections 1 and 2.1 (first researcher) placed the chat model
selector "at the top of a chat". It is rendered only inside the message composer, bottom right
(`src/lib/components/chat/MessageInput.svelte:2576-2583`; `Navbar.svelte` does not include it).
Found by the continuation agent, verified in the main loop, corrected in place on 2026-10-08.

### 4. Precision Notes Added After Verification (Reference Layer)

- `workspace-models-and-model-access.md` section 3.3: a provider model without a record already
  shows as enabled; the first toggle switches it off and creates a disabled record with no access
  entries (`src/lib/components/admin/Settings/Models.svelte:304-311`, `:514-525`).
- `users-groups-roles-and-permissions.md` sections 3.2 and 3.7: admins without the bypass see
  record-less base models only while no Model Defaults metadata is stored
  (`backend/open_webui/utils/models.py:341-347`, `:533-536`, `:563-574`).

### 5. Valves Described as Stored Encrypted (Ground-Truth Layer)

`ground-truth.md` (Secrets) said tool and function valves "are stored encrypted in the database",
and `CLAUDE.md` said the same. The code encrypts valves only when `ENABLE_VALVE_ENCRYPTION` is on,
and its default is off (`backend/open_webui/env.py:767`; `backend/open_webui/utils/valves.py:22-24`).
Found by the workspace-tools researcher (who wrote its document to the code and flagged the
discrepancy rather than following ground truth), verified in the main loop, corrected in both files
on 2026-10-08. The claim had been carried over from the pre-existing `CLAUDE.md` into ground truth
without being re-read against the source.

### 6. A Persistent Setting Described as Environment-Only (Reference Layer)

`builtin-native-tools.md` section 7 said `web.fetch.max_content_length` is changed through the
environment. It is a persistent setting that admins edit at Admin Settings › Web Search › **Fetch URL
Content Length Limit** (`src/lib/components/admin/Settings/WebSearch.svelte:1171-1177`;
`backend/open_webui/config.py:2950`). Found by the web-search researcher reading a neighbouring
document, verified in the main loop, corrected in place on 2026-10-08.

### 7. Memory Batch Types (Reference Layer)

`memories.md` section 4.2 (first researcher) said a background-review or `update_memory` operation
with any type other than `user` is stored as `context`. The request form accepts only `user`,
`context` or no type (`backend/open_webui/routers/memories.py:85-90`, a `Literal` field), so any
other value refuses the whole batch and none of its operations is applied. Corrected in place by
the continuation agent under rule 21 on 2026-10-09 and verified in the main loop.

### 8. Two Function-Workflow Details (Reference Layer, Pending Main-Loop Check)

`functions-pipes-filters-actions-and-pipelines.md` sections 5.3 and 5.6 were corrected in place by
the continuation agent under rule 21 on 2026-10-09: an imported function carries its whole `meta`
object (translations included), and `Error fetching valves` appears only when the server returns
error text, while a function whose code fails to load shows `No valves` and is switched off. Not
yet re-checked in the main loop; scheduled for the Phase 4 claim review.

### 9. Skills Picked From the Slash List (Reference Layer, Read From Code)

`prompts-and-skills.md` sections 1 and 4.4 (first researcher) and `chat-composer-and-message-display.md`
section 5.8 said a skill picked from the `/` list behaves like a `$` mention. The server only
recognizes `<$id…>` or `</id|…>` (`backend/open_webui/utils/skills.py:10`), the editor's mention
chip defaults to the `@` marker (`node_modules/@tiptap/extension-mention/src/mention.ts:216-217`, an
installed library), and the chat's `/` handler inserts the chip without setting it
(`src/lib/components/chat/MessageInput.svelte:1450-1459`). The continuation agent corrected the
prompts document under rule 21 on 2026-10-09; the main loop verified the regex and the default and
added a marked precision note to the composer document. Whether the `/` list passes a marker in
its properties remains to be confirmed in a test environment.

### 10. Citation Past the End of a File (Reference Layer)

`channels-and-direct-messages.md` section 9.3 (first researcher) cited
`backend/open_webui/routers/notifications.py:227`, a line past the end of that 103-line file;
`validate.py` exits 1 on this. The real source is `backend/open_webui/utils/notifications.py:223-231`.
Fixed in place by the continuation agent under rule 21 on 2026-10-10. The same pass corrected two
claims in sections 3.1 and 9.2 (live-update room membership is checked against code defaults;
browser notifications require a visible tab, window focus is checked only in the desktop app),
which await a main-loop re-check in Phase 4.

### 11. Three Audio Workflow Details (Reference Layer)

`audio-speech-to-text-and-text-to-speech.md` (first researcher) said a call needs exactly one model,
that noise always interrupts an answer, and that the slim image offers only outside speech services.
Corrected in place by the continuation agent under rule 21 on 2026-10-10: a call is refused only
with more than one model selected (`src/lib/components/chat/MessageInput.svelte:2679`, verified in
the main loop); noise interrupts an answer only with **Allow Voice Interruption in Call** on, which
defaults to off (`src/lib/components/common/InterfaceSettings.svelte:106`, `:333`;
`src/lib/components/chat/MessageInput/CallOverlay.svelte:323`, verified); browser speech and
Kokoro also work in the slim image (not yet re-checked in the main loop).

### 12. An Unreachable Status Described as Reachable (Reference Layer)

`chat-completion-pipeline-and-generation-tasks.md` section 10 and its failure table described
`Image generation is disabled` as the status shown when image generation is requested while off. With
generation off and no edit, the step returns earlier with no status
(`backend/open_webui/utils/middleware.py:1866-1868`); the branch that emits the text (`:1935-1946`)
is reached only if the setting changes between two reads. Found by the image-generation researcher,
verified in the main loop, corrected in place on 2026-10-10. The same research showed that the
`DATA_DIR/cache/image/generations` folder named in the image brief and in ground truth's cache row
is created but unused (`backend/open_webui/routers/images.py:54-55`); ground truth refined.

### 13. Analytics Location and a Mis-Attributed Source (Reference Layer)

`evaluations-feedback-and-analytics.md`: its At a Glance placed the analytics dashboards at
`/admin/analytics`, which in v0.11.4 only redirects to the Settings window
(`src/routes/(app)/admin/analytics/+page.svelte:6-12`); verified and corrected in the main loop on
2026-10-10 (the document's section 2.1 already had it right). Its section 8 attributed "there is no
crontab" to ground truth; the statement comes from `CLAUDE.md` and was re-confirmed by search. Both
are minor; corrected in place.

### 14. Never-Shown Messages and a Status Code (Reference Layer)

The backend content catalogue found texts that can never reach a user. Two corrected other
documents: `rag-retrieval-embeddings-and-vector-stores.md` section 10.1 listed
`Configure CHROMA_HTTP_HOST: embedded Chroma is unavailable in slim.` as reachable, but in the slim
image the vector factory refuses every store except pgvector first
(`backend/open_webui/retrieval/vector/factory.py:20-24`; verified in the main loop, corrected in
place); and the open question in `model-connections-openai-ollama-and-direct.md` about
`OpenAI API was not found` was resolved (the message function is passed uncalled at
`backend/open_webui/routers/openai.py:673`, so callers get a bare server error). Within the catalogue,
section 3.1 was corrected under rule 21: a calendar-recurrence time-out while saving an event answers
422 from the calendar router (`backend/open_webui/routers/calendar.py:278-279`), and the global 400
handler applies only to uncaught time-outs.

### 15. An Unreachable Registration Message and Refusal Wording (Reference Layer)

`sso-oauth-oidc-and-scim.md` section 10 listed `Dynamic client registration failed`
(`backend/open_webui/utils/oauth.py:641`) as shown when registration ends without an answer. The
registration address is always set (`:585-590`) and the request block always returns or raises before
line 641, so the line is dead code; a connection failure raises the HTTP library's own error. Found
by the backend identity catalogue, verified in the main loop, corrected in place on 2026-10-10. The
catalogue also corrected its own section 4.6 under rule 21: most `401 Unauthorized` uses in the
content routers are missing feature or workspace permissions, the rest missing write access, not
"ownership refusals".

### 16. In-Chat Status Details (Reference Layer, Pending Main-Loop Check)

`in-chat-status-and-response-messages.md` was corrected by its continuation agent under rule 21 on
2026-10-10: the core `Searched {{count}} sites` event carries no `query`, so no search link is shown
(site icons still load from Google's favicon service); current replies do not draw a waiting
ask-user call at all, and `Input needed` appears only for replies drawn from `<details>` text; the
error box is light grey, not red, and status wording follows each viewer's interface language. Not
yet re-checked in the main loop (Phase 4).

### 17. Start-Up Log Line Attribution (Reference Layer, Pending Main-Loop Check)

`configuration-environment-variables-bootstrap.md` section 5.2 attributed the `GLOBAL_LOG_LEVEL`
start-up line to `backend/open_webui/env.py`; that line prints only when the variable is set, and
the line every worker prints comes from `backend/open_webui/utils/logger.py:223`. Corrected in place
by the continuation agent under rule 21 on 2026-10-10; pending main-loop re-check in Phase 4.

### 18. Three Admin-Panel Feedback Claims (Reference Layer)

`admin-settings-panels.md` said the webhook save could show the server's text, that `OpenAI URL/Key
required.` covers the OpenAI and Azure engines, and that Web Search and Code Execution show
"Settings saved successfully!" only after success. The code shows: the webhook API client throws
the parsed response object, so the generic `Failed to save webhook` always appears
(`src/lib/apis/index.ts:1656-1675`; `src/lib/components/admin/Settings/Events.svelte:357`); the
URL/Key text is in the Azure OpenAI branch only
(`src/lib/components/admin/Settings/Documents.svelte:109-113`); and a save failure without a server
reason returns `null` instead of throwing (`src/lib/apis/retrieval/index.ts:84-91`), so the success
pop-up still appears. Found by the front-end admin catalogue, verified in the main loop, corrected in
place on 2026-10-10.

### 19. Two Persistence Details (Reference Layer, Pending Main-Loop Check)

`configuration-persistent-settings-a-to-o.md` section 2.2 (first researcher) was corrected in place
by the continuation agent under rule 21 on 2026-10-11: the audio settings endpoint reads and accepts
all 30 `audio.*` keys (only the screen omits `audio.stt.allowed_extensions`), and `/api/config` sends
the feature switches to every signed-in account including `pending` ones, limiting only the engine
names and later blocks to `user` and `admin`. Pending main-loop re-check in Phase 4.

### 20. Exceptions to "the Stored Value Wins" and Two Save Side Effects (Ground Truth and Reference Layer)

The `r-to-w` persistent-settings catalogue found three refinements: `ui.default_locale` is stored but
never read (the environment constant is sent instead; `backend/open_webui/main.py:2315`, verified),
web-loader keys stored as `null` fall back to the environment
(`backend/open_webui/retrieval/web/utils.py:1065-1068`, verified), and `RAG_FILE_MAX_SIZE` also sets
an environment-only metadata limit (not re-checked). Ground truth refined on 2026-10-11. It also found
that saving the Documents panel re-posts the `web` block it loaded
(`src/lib/components/admin/Settings/Documents.svelte:264-265`, verified that the whole loaded config
is spread into the request) and that a failed reranker load saves hybrid search as off; precision
notes were added to `web-search-and-web-loading.md` section 7.7 and
`rag-retrieval-embeddings-and-vector-stores.md` section 7.10.

### 21. Start-Up, Readiness and Cookie Claims (Reference Layer)

Found by the backend architecture researcher and verified in the main loop on 2026-10-11:
`configuration-environment-variables-bootstrap.md` said a mistyped `AUDIT_LOG_LEVEL` leaves auditing
off, but the error path calls `logger.error` on a module without that attribute
(`backend/open_webui/main.py:211`, `:800`), so start-up fails (product defect 13); that document and
`error-messages-backend-identity-admin-and-platform.md` described `/ready` answering
`Startup not complete` during start-up, but uvicorn opens its port only after start-up
(`.venv` uvicorn 0.51.0, `server.py:104` before `:142`), so probes see no connection or wait; and
`authentication-and-sign-in.md` section 5.8 says every 401 deletes the `token` cookie, which is
doubtful because FastAPI discards the injected response when a dependency raises (marked for a
test). All four passages corrected or annotated in place.

## Residual Flags and Why They Are Benign

| Category | Count | Example | Why benign |
|---|---|---|---|
| Message composed from a constant template and a known argument | 5 | `Search query generation is disabled` | Built from `ERROR_MESSAGES.FEATURE_DISABLED('Search query generation')` and `f'{name} is disabled'` (`backend/open_webui/routers/tasks.py:410`, `backend/open_webui/constants.py:125`); the document cites both lines. Also a start-up message about code-challenge methods (`backend/open_webui/config.py:2643-2648`) and three log lines quoted with the exception text filled in, `Error processing chat metadata: Model not found` and `Error processing chat payload: Model not found` (`backend/open_webui/main.py:1641`, `:1688`) |
| Deliberate citation of a missing file | 2 | `knowledgebase/tools/verification-baseline.txt`; `src/lib/components/admin/Settings.svelte` | This file cites the baseline before Phase 4 writes it, and names the non-existent file in mistake 4 on purpose |
| Interface text rendered with a hard-coded interpolation value | 2 | `Enter model tag (e.g. mistral:7b)` | The source is `Enter model tag (e.g. {{modelTag}})` with `mistral:7b` and `my-modelfile` passed literally (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:655-656`, `:873-874`); the document quotes what the admin sees |

## Database Verification (Schema Only, Local Development Copy)

Read on 2026-10-07 with `db_select.sh` in read-only `sqlite` mode against the maintainer's local
development database; structure and key names only, no row contents, not production.

1. Applied migration `d4c1a8e37b62`, equal to the repository head.
2. 43 tables: the 39 model tables, `alembic_version`, and the legacy `chatidtag`, `document` and
   `config_old` that the migration history predicts.
3. `config`: 352 rows; every stored key is a known `DEFAULT_CONFIG` key and the 53 absent keys are
   exactly the `oauth.*` keys, confirming that OAuth settings are not stored while
   `ENABLE_OAUTH_PERSISTENT_CONFIG` is off.
4. Columns of all 39 model tables match their SQLAlchemy definitions except `knowledge.data`,
   dropped by migration `3e0e00844bb0`, re-added by `81cc2ce44d79`, and unmapped by the v0.11.4
   model (a benign leftover).

## Mistakes Made While Checking

1. A `CLAUDE.md` draft placed the fork's two settings in `UserSettings`; they are in the
   `InterfaceSettings` model (`backend/open_webui/models/users.py:99-100`). Caught on re-reading.
2. The first config-key count was 404 because the inventory regex required a dot; `DEFAULT_CONFIG`
   has 405 (`webhook_url` has none). A whole-file regex would have counted 414. Fixed with a
   `within` block limit in `kbconfig.regex_names`.
3. `CLAUDE.md` cited `config.py:3230` for `ENABLE_OAUTH_PERSISTENT_CONFIG`; the line is 3232.
4. `../reference/_areas.md` listed a file that does not exist
   (`src/lib/components/admin/Settings.svelte`); caught by `validate.py` on its first run.
5. Recursive counts first counted distinct file names (554 Svelte files instead of 671) because
   `list_scope` de-duplicates names unless `relative` is set.
6. Unquoted `--include=*.py` broke under zsh globbing; include patterns must be quoted.
7. `check_sections.py` rejected the template's own heading `## At a Glance`; it now matches
   case-insensitively.
8. Researchers running in parallel overwrote each other's temporary files in the shared scratchpad;
   the research instructions now require a per-slug sub-folder.
9. Two usage-limit interruptions stopped seven researchers mid-write. Progressive writing preserved
   every document; final summaries were lost, so gaps are harvested from section 14 of each file.
10. Continuation briefs said "do not rewrite anything that exists", which is stricter than the
    additive rule; one continuation agent therefore left a wrong claim it had found and only noted it
    in section 14. Corrections to verified errors are allowed in place; later briefs say so.
11. A Phase 1 ground-truth fact (valve encryption) was copied from the existing `CLAUDE.md` without
    verification. Inherited claims need the same check as new ones.
12. The quote corpus covered only the `backend`, `src` and `scripts` directories, so a message quoted
    exactly from `Dockerfile:138` was flagged as missing (the same lesson as the method's pitfall 5).
    `verify_quotes.py` now also reads the repository-root files listed in `source.extra_files`.
13. Quotes inside Markdown table cells escape `|` as `\|`, so a verbatim text containing a pipe was
    flagged. `verify_quotes.py` now unescapes `\|` before matching.

## How to Reproduce

```bash
bash knowledgebase/tools/run_all_checks.sh --quotes
python3 knowledgebase/tools/verify_quotes.py --diff knowledgebase/tools/verification-baseline.txt
```

The baseline file is written at the end of Phase 4.

## What Was Not Verified

Live data, server state, anything marked TO BE CONFIRMED, behaviour that needs a running
application, and that cited lines still say what the documents claim after the next release.
