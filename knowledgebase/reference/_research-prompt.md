# Research Instructions for One Reference Area

Not a reference document (underscore prefix). These are the standing instructions every Phase 2
researcher followed, filled in for this application. The per-area title, slug, scope and focus
come from [`_areas.md`](_areas.md). Re-use this file verbatim when re-researching an area after a
release.

---

You are documenting one area of **MedIT GPT**, the University of Toronto deployment of **Open
WebUI v0.11.4** (repository root `/Users/sam/Sites/open-webui`, branch `uoft`), for a tier-1
support knowledgebase.

## Project Context

Read these first, in order: `CLAUDE.md`, `knowledgebase/tools/ground-truth.md`,
`knowledgebase/tools/inventory.md`. Every fact in them is verified; do not contradict them and do
not re-derive them. If you find something in the code that seems to contradict them, say so in
section 14 and in your final summary rather than silently choosing.

## Output

Write `knowledgebase/reference/<slug>.md` and **nothing else**. Do not modify any other file: no
source file, no other knowledgebase file, no git operation that changes state. Do not start the
application and do not query any database.

Write **progressively** so partial work survives an interruption:

1. Create the file with the Write tool containing only the `# Title` and the `## At a Glance`
   section **within your first few minutes, before any deep reading**. A provisional At a Glance of
   three or four bullets from the scope and focus is fine; refine it with the Edit tool at the end.
   Then write each section as soon as its research is done rather than researching everything
   first. Researchers who read for half an hour before writing have lost all their work to a
   usage limit.
2. Append each numbered section as you finish it with a quoted heredoc, which keeps backticks and
   `$` intact:
   ```bash
   cat >> knowledgebase/reference/<slug>.md <<'EOF'

   ## 1. Purpose and Who Uses It
   ...
   EOF
   ```
3. Never rewrite the file from scratch once sections exist. To fix an earlier section, use the
   Edit tool on that passage only.

## Structure

Exactly these headings, numbered, in this order, none omitted. Write "None found in code" (with a
sentence on what you searched) rather than skipping a section.

```
# <Area Title>
## At a Glance
## 1. Purpose and Who Uses It
## 2. Navigation and URLs
## 3. Roles and Permissions
## 4. Key Concepts and Terminology
## 5. Workflows (Step by Step)
## 6. Data Model
## 7. Settings and Configuration
## 8. Cron Jobs and Background Processes
## 9. Notifications and Emails
## 10. Error, Warning and Notice Messages (Verbatim)
## 11. Common Tier-1 Issues and Troubleshooting
## 12. Local Customisations
## 13. Source File Index
## 14. Open Questions
```

Sub-headings inside a section use `###` and are numbered `### 5.1 ...`, `### 5.2 ...`.

## Rules

1. **Ground every claim** in a file and cite it as `path:line` (repository-relative, for example
   `backend/open_webui/routers/auths.py:412` or `src/lib/components/chat/Chat.svelte:880`). A claim
   you cannot trace goes in section 14, not in the body.
2. **Quote every user-facing message verbatim**, including odd spacing, punctuation, emoji and
   placeholders, with its `file:line` and the condition that triggers it.
3. **Be exhaustive within your scope.** List the directories in scope so nothing is missed; read
   files fully or in chunks; never summarize a file you have not opened.
4. **Harvest messages in bulk** with `grep -rn`, then open a file only to establish a trigger
   condition or resolve a translation key. Message sources in this codebase:
   - backend: `raise HTTPException(` with `detail=`; `ERROR_MESSAGES.<NAME>` (text in
     `backend/open_webui/constants.py`); f-string details; status events sent through an event
     emitter (`'type': 'status'` with `'description'`); `'type': 'notification'` events;
     `log.error`/`log.warning` only when they explain a symptom (label them as log lines, not
     user messages);
   - front end: `toast.error(`, `toast.success(`, `toast.warning(`, `toast.info(`, `$i18n.t('...')`,
     `confirm(`, `ConfirmDialog` titles and messages, and visible text in markup.
5. **Translations.** Plain i18n keys are the English text itself (`$i18n.t('Chat deleted.')`
   displays `Chat deleted.`). Dotted keys (for example
   `settings.personal.interface.hideProcessingDetails.label`) have their English text **only** in
   `src/lib/i18n/locales/en-US/translation.json`; quote that English text and cite both the
   component line and the `translation.json` line. Do not read other locale files.
6. **Where backend text surfaces.** A backend `detail` usually reaches the user through a front-end
   toast that prints the error; when you can establish which component shows it, say so.
7. **Never invent** a contact, URL, host, schedule, service level, organisation name, table,
   column, setting or message. Anything organisational the code cannot prove is written
   **TO BE CONFIRMED**. The production host name is TO BE CONFIRMED; write URLs relative to the
   site root (`/admin/settings/general`).
8. **No personally identifiable information.** No names, usernames, ids, addresses, git author
   names or `@author` values. Invent examples and make them obviously fictional
   (`jane.doe@example.com`). **Never open `backend/data/`** (it holds the local database, uploads
   and vector store, which may contain personal and health information) and **never open any
   `.env` file**. Never reproduce a secret; cite its location only.
9. **Code versus data.** Defaults in code, seed values and configuration arrays are what the
   repository says; the live value of any setting is data held in the database `config` table (or
   the environment) and must be marked as such.
10. **Working tree.** The `uoft` branch is three commits on top of upstream v0.11.4 (`main` equals
    upstream). The working tree also has uncommitted changes in
    `src/lib/components/chat/Chat.svelte`,
    `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte`,
    `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte`,
    `src/lib/components/chat/Messages/ResponseMessage.svelte`,
    `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte`,
    `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte`,
    `src/lib/components/chat/Messages/structuredOutput.ts`,
    `src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/i18n/index.ts` and
    `src/lib/i18n/locales/en-US/translation.json`. Cite files as they are in the working tree now.
    For section 12 use read-only `git diff main...uoft -- <paths>` and `git diff -- <paths>`; if
    nothing in scope differs, write that the area matches upstream v0.11.4.
11. **No email, no crontab.** The backend contains no email-sending code. Section 9 covers in-app
    notifications, browser notifications, webhooks and socket events instead (or says none
    exist). Section 8 covers in-process background loops, background tasks and Redis listeners;
    there is no crontab. Say when something happens at save time rather than in the background.
12. **Placeholders.** Write an interpolated value as `{name}` using the source's variable name, for
    example `Model '{name}' was not found`; quote everything else exactly.
13. **Section 10** is a table, first cell the backticked verbatim message:
    `| Message | Severity | Source | Trigger | User action | Support check |`. One row per distinct
    message per source file; put additional lines in the Source cell.
14. **Section 11.** Each symptom is a heading phrased as a user would say it,
    `### 11.1 "I can't sign in with my email and password"`, followed by **Symptom.**, **Likely
    causes, in order.**, **Diagnostic steps** (read-only), **Resolution** (what tier 1 may do;
    tier 1 is read-only and never changes data, settings, roles or access, so the resolution is
    usually guidance or an escalation), **Escalation** (what to send, with identifiers).
15. **Audience.** Write for a technical non-developer: plain sentences first, then the evidence.
16. **House style.** Headings in Title Case; body copy in sentence case; Canadian spelling (colour,
    behaviour, centre, catalogue, licence as a noun, -ize verbs such as organize). Verbatim
    messages are quoted as the code spells them.
17. **Absolutes.** Prefer "the code does X" over "X always happens". Every "never", "always" and
    "cannot" you write will be audited against the source.
18. **Length.** Be thorough; most documents run 600 to 1,500 lines and catalogues longer. Depth
    beats brevity, but every line must be grounded. Prefer tables to prose, state each fact once
    and cross-reference other sections rather than repeating it.
18a. **Section 14 is the record of your gaps.** Your final reply can be lost if the session hits a
    usage limit, so every gap, unknown and TO BE CONFIRMED item must also appear in section 14 of
    the document. Finish any correction you start before moving on, so an interruption never
    leaves a half-applied fix.
19. Do not use sub-agents.
19a. **Temporary files.** Several researchers run at once and share one scratchpad directory. Put
    any temporary file (citation lists, grep output, helper scripts) only in a sub-folder named
    after your slug, for example `<scratchpad>/<slug>/cited.txt`, never directly in the scratchpad,
    so concurrent researchers cannot overwrite each other's files.
20. **Security-sensitive detail stays out.** Do not document how credentials or keys are stored,
    hard-coded or default credentials, ways to bypass authentication or access control,
    unauthenticated or debug-only endpoints, token-handling weaknesses, or anything that reads as
    an attack recipe. Describe what users and admins see and do, and the settings that govern it.
    Where a security question arises, write "Security-sensitive: refer to the platform maintainer
    and U of T Information Security (security.utoronto.ca)" and list it in your gaps **without**
    the detail. Personal data in logs, exports and admin views may be described as such (for
    example "the audit log contains user emails"), because support must handle it with care.

## Continuing or Repairing Another Researcher's Document

21. Never rewrite, reorder or delete existing text. Append missing sections at the end. If you
    verify that an earlier claim is wrong, correct that passage in place with the Edit tool, keep
    the surrounding content, and mark it `*Corrected <date>: …*`; list the correction in your reply.

## When Finished

Reply with a structured summary: the sections written (with sub-headings), the count of verbatim
messages quoted, the files read, and a **gaps** list of everything you could not establish from
the code and why. The gaps list is the most valuable part of your report.
