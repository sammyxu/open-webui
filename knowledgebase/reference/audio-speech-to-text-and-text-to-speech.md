# Audio: Speech-to-Text, Text-to-Speech and Voice Calls

## At a Glance

- *Provisional; refined at the end of research.*
- MedIT GPT turns speech into text (dictation in the message composer, transcription of uploaded audio files) and text into speech ("read aloud" on responses), and offers a hands-free voice call mode that chains the two.
- Administrators choose the speech-to-text and text-to-speech engines in the admin Audio settings (stored as `audio.*` configuration keys); each user can override some choices in their personal Audio settings.
- Three permissions, `chat.stt`, `chat.tts` and `chat.call`, decide whether a non-admin user sees the microphone, read-aloud and call controls.
- Generated speech is cached on the server under `DATA_DIR/cache/audio/`; cached audio contains chat content and must be treated as personal data.
- *Added 2026-10-10 when sections 10 to 14 were completed:*
- Most user problems are browser permission or browser support questions (sections 11.2, 11.10, 11.13); the rest
  depend on the administrator's engines, which a user's own Settings > Audio page reveals (section 11).
- Several failures show no message at all: speech failures during calls, admin save refusals, Kokoro load failures
  and requests that fail without a readable error (sections 10.7, 10.10).
- Speech errors can say "Open WebUI" (the licence-protected upstream name) or begin `External:` (the outside
  service's own text) (section 10.5).
- The audio area matches upstream v0.11.4; no fork change touches it (section 12).

## 1. Purpose and Who Uses It

MedIT GPT has four voice features. All of them are built from two server services, **speech-to-text**
(turning a recording into text, also called transcription or STT) and **text-to-speech** (turning text into
spoken audio, also called TTS), or from the equivalent services built into the user's web browser.

| Feature | What the user does | Uses | Where in the code |
|---|---|---|---|
| **Dictate** | Clicks the microphone in the message composer, speaks, confirms; the words appear in the text box | Speech-to-text | `src/lib/components/chat/MessageInput.svelte:2629-2668`, `:1735-1758`; `src/lib/components/chat/MessageInput/VoiceRecording.svelte` |
| **Read Aloud** | Clicks the speaker button under an answer; the answer is spoken | Text-to-speech | `src/lib/components/chat/Messages/ResponseMessage.svelte:250-390` |
| **Voice mode** (a voice call) | Clicks the round voice button in an empty composer and talks hands-free; each pause sends what was said and the answer is spoken back | Both, in a loop | `src/lib/components/chat/MessageInput.svelte:2671-2733`; `src/lib/components/chat/MessageInput/CallOverlay.svelte` |
| **Transcription of an uploaded recording** | Attaches an audio file (or a `video/webm` file) to a chat or knowledge base; the transcript becomes the file's text | Speech-to-text | `backend/open_webui/routers/files.py:152-165` |

The same dictation bar is reused outside the chat composer: in the channel composer
(`src/lib/components/channel/MessageInput.svelte:776`), in the notes editor
(`src/lib/components/notes/NoteEditor.svelte:1473`) and in the knowledge-base "add text content" window
(`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:82`). Notes also have their own
recording menu, documented in `notes.md`.

**Who uses it.**

- **Users** dictate, listen to answers, hold voice calls and upload recordings. Each user can change a few
  personal choices in **Settings > Audio** (the browser or server engine for their own device, the voice, the
  speed, auto-send and auto-play), described in section 7.2
  (`src/lib/components/chat/Settings/Audio.svelte`).
- **Administrators** choose which speech-to-text and text-to-speech services the server uses, enter their
  addresses and keys, and pick the default voice and model, in **Admin Panel > Settings > Audio**
  (`src/lib/components/admin/Settings/Audio.svelte`). The choices are stored as the 30 `audio.*` persistent
  settings (`backend/open_webui/config.py:3052-3081`). Administrators also decide, per group, whether users may
  use speech-to-text, text-to-speech and voice calls (`chat.stt`, `chat.tts`, `chat.call`; section 3). A custom
  model can carry its own default voice (`src/lib/components/workspace/Models/TTSVoiceInput.svelte`).
- **Tier 1 support** mostly meets this area as "the microphone does nothing", "read aloud is silent", "the call
  keeps cutting out", "the transcript is in the wrong language" and "the file is too large" (section 11). Most
  of these are browser permission or browser support questions; the rest depend on which engines the
  administrator chose, which is live configuration (**TO BE CONFIRMED** for production).

**Privacy in one paragraph.** Depending on the engine, the user's voice and the text of answers are sent to an
outside service (OpenAI-compatible, Azure, Deepgram, ElevenLabs, Mistral), processed on the MedIT GPT server
(local Whisper, local SpeechT5), or processed only in the user's browser (browser speech, Kokoro). Recordings,
transcripts and generated speech are also kept in the server cache (section 6). MedIT GPT chats may contain
health information, so cached audio and transcripts must be handled as personal data. Which engines production
uses, and whether any outside service has been approved for this data, is **TO BE CONFIRMED**.

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Screens and Controls

| Where | How to get there | What is there | Source |
|---|---|---|---|
| **Dictate** microphone | Message composer on `/` (new chat) or `/c/{id}` (existing chat), right-hand side, shown only when no answer is being written | Opens the dictation bar (section 5.1) | `src/lib/components/chat/MessageInput.svelte:2629-2668` |
| **Voice mode** button | Same place, shown instead of **Send message** while the text box is empty and nothing is attached | Opens the voice call (section 5.3) | `src/lib/components/chat/MessageInput.svelte:2671-2733` |
| Voice call screen | Opens in the right-hand side panel on a large screen, or as a full-screen drawer on a small screen | The model's picture or a camera view, a status line, and **Camera**, **Mute** and **End call** buttons (section 5.3) | `src/lib/components/chat/ChatControls.svelte:196-216`, `:328-339`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:975-1143` |
| **Read Aloud** | Speaker icon in the row of buttons under each answer | Speaks the answer; click again to stop | `src/lib/components/chat/Messages/ResponseMessage.svelte:1146-1232` |
| Personal **Settings > Audio** | Profile menu > **Settings**, then **Audio** in the **Preferences** group | Personal speech-to-text and text-to-speech choices (section 7.2) | `src/lib/components/chat/SettingsModal.svelte:150`, `:229-234`, `:832-838` |
| **Admin Panel > Settings > Audio** | Same Settings window, **Audio** in the admin **Experience** group (administrators only) | Server engines, keys, voice, model, splitting (section 7.1) | `src/lib/components/chat/SettingsModal.svelte:171`, `:304-309`, `:885-890` |
| Dictation in other places | Channel composer, notes editor, knowledge base **Add text content** window | The same dictation bar | `src/lib/components/channel/MessageInput.svelte:776`; `src/lib/components/notes/NoteEditor.svelte:1473`; `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:82` |
| Model default voice | **Workspace > Models**, edit a model, the voice field | A voice used for that model's answers (section 7.4) | `src/lib/components/workspace/Models/ModelEditor.svelte:258`; `src/lib/components/workspace/Models/TTSVoiceInput.svelte` |

The two Audio tab titles are dotted i18n keys: `settings.personal.audio.title` and `settings.admin.audio.title` both
read `Audio` (`src/lib/i18n/locales/en-US/translation.json:2796`, `:2008`). The personal Audio tab is offered to
every signed-in user; the code applies no permission to it (`src/lib/components/chat/SettingsModal.svelte:379-411`).

### 2.2 Deep Links

| Link | Effect | Source |
|---|---|---|
| `/?settings=audio` | Opens the Settings window on the personal Audio tab | `src/routes/(app)/+layout.svelte:166-195` |
| `/?settings=admin:audio` | Opens the admin Audio tab; a non-administrator gets the personal **General** tab instead | `src/routes/(app)/+layout.svelte:181-185` |
| `/admin/settings/audio` | Redirects to `/?settings=admin:audio` | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10` |
| `/?call=true` (also on a chat URL) | Opens the voice call screen when the chat loads; the microphone check and the one-model check of the button (section 5.3) are skipped | `src/lib/components/chat/Chat.svelte:2008-2013`, `:2207-2209` |

### 2.3 Keyboard Shortcut

**Cmd+Shift+L** (Ctrl+Shift+L on Windows) starts dictation, and while recording confirms it, by clicking the same
buttons a mouse would. It is ignored when the user has turned keyboard shortcuts off
(`src/lib/shortcuts.ts:25`, `:90`; `src/lib/components/chat/MessageInput.svelte:1328-1342`).

### 2.4 Server Endpoints

The audio router is mounted at `/api/v1/audio` (`backend/open_webui/main.py:851`); the browser calls it through
`src/lib/apis/audio/index.ts` (base URL `src/lib/constants.ts:15`).

| Method and path | Who may call it | What it does | Source |
|---|---|---|---|
| `GET /api/v1/audio/config` | Administrators | Reads the speech-to-text and text-to-speech settings | `backend/open_webui/routers/audio.py:282-287` |
| `POST /api/v1/audio/config/update` | Administrators | Saves them; reloads local Whisper when it is selected | `backend/open_webui/routers/audio.py:290-323` |
| `POST /api/v1/audio/speech` | Signed-in users with `chat.tts` (administrators always) | Turns text into speech (MP3 by default) | `backend/open_webui/routers/audio.py:601-667` |
| `POST /api/v1/audio/transcriptions` | Signed-in users with `chat.stt` (administrators always) | Turns an uploaded recording into text | `backend/open_webui/routers/audio.py:1251-1341` |
| `GET /api/v1/audio/models` | Signed-in users | Lists text-to-speech models offered by the configured engine | `backend/open_webui/routers/audio.py:1404-1406` |
| `GET /api/v1/audio/voices` | Signed-in users | Lists voices offered by the configured engine | `backend/open_webui/routers/audio.py:1509-1511` |

Recordings attached as files go through `POST /api/v1/files/` instead and are transcribed by the same server code
(`backend/open_webui/routers/files.py:152-165`; see `files-uploads-and-storage.md`).

## 3. Roles and Permissions

### 3.1 The Three Speech Permissions

Speech has three switches in the `chat` section of the user permissions. Each is on by default, seeded from an
environment variable, and editable per group in **Admin Panel > Users > Groups** (the default permissions and each
group's permissions). As for every permission, a user has it if any of their groups grants it or the default grants
it; a group cannot take away a permission the defaults grant (see `users-groups-roles-and-permissions.md`).

| Permission | Switch label (verbatim) | Code default | Seeded from | What it controls | Source |
|---|---|---|---|---|---|
| `chat.stt` | `Allow Speech to Text` | on | `USER_PERMISSIONS_CHAT_STT` | The **Dictate** microphone, and the server's transcription endpoint | `backend/open_webui/config.py:1889`, `:1994`; `src/lib/components/admin/Users/Groups/Permissions.svelte:849-863`; `src/lib/components/chat/MessageInput.svelte:2630`; `backend/open_webui/routers/audio.py:1258-1262` |
| `chat.tts` | `Allow Text to Speech` | on | `USER_PERMISSIONS_CHAT_TTS` | The **Read Aloud** button, and the server's speech endpoint | `backend/open_webui/config.py:1891`, `:1995`; `src/lib/components/admin/Users/Groups/Permissions.svelte:865-879`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1146`; `backend/open_webui/routers/audio.py:612-616` |
| `chat.call` | `Allow Call` | on | `USER_PERMISSIONS_CHAT_CALL` | The **Voice mode** button | `backend/open_webui/config.py:1893`, `:1996`; `src/lib/components/admin/Users/Groups/Permissions.svelte:881-895`; `src/lib/components/chat/MessageInput.svelte:2671` |

When a group switch is off but the default grants the permission, the group editor shows
`This is a default user permission and will remain enabled.` under the switch
(`src/lib/components/admin/Users/Groups/Permissions.svelte:856-862`, `:872-878`, `:888-894`). The browser also
treats a missing value as on (`src/lib/constants/permissions.ts:55-57`; the `?? true` in the checks above).

### 3.2 What Each Role Gets

| Role | Dictate, Read Aloud, Voice mode | Admin Audio settings | Source |
|---|---|---|---|
| `admin` | Always shown and always allowed by the server, whatever the permissions say | Yes | `src/lib/components/chat/MessageInput.svelte:2630`, `:2671`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1146`; `backend/open_webui/routers/audio.py:612`, `:1258`; `backend/open_webui/routers/audio.py:282-291` |
| `user` | Shown and allowed when the matching permission is granted | No (the admin tab is not offered; the admin endpoints refuse) | `src/lib/components/chat/SettingsModal.svelte:406-410`; `backend/open_webui/utils/auth.py` (`get_admin_user`) |
| `pending` | None: a pending account cannot use the chat, and the speech endpoints require a signed-in `user` or `admin` | No | `backend/open_webui/routers/audio.py:602`, `:1256` (`get_verified_user`) |

### 3.3 What a User Sees When a Permission Is Off

- **`chat.stt` off:** the microphone button is not drawn in the chat composer
  (`src/lib/components/chat/MessageInput.svelte:2630`). If a transcription request still reaches the server it is
  refused with HTTP 403 and `You do not have permission to access this resource. Please contact your administrator for assistance.`
  (`backend/open_webui/routers/audio.py:1258-1262`; `backend/open_webui/constants.py:70-72`). The other screens
  that offer dictation do not look at `chat.stt` before drawing their microphone: the channel composer shows
  **Record voice** whenever its text box is empty (`src/lib/components/channel/MessageInput.svelte:1021-1025`),
  the notes editor shows its record menu to anyone who can edit the note
  (`src/lib/components/notes/NoteEditor.svelte:1157-1158`), and the knowledge-base text window always shows
  **Voice Input** (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:97-104`). With a
  server engine the recording is then refused by the server and the user sees the permission text as a red
  pop-up (section 5.1); with the browser engine (`Web API`) the words are recognised by the browser itself and
  no server check is involved.
- **`chat.tts` off:** no **Read Aloud** button under answers
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:1146`); a speech request is refused with HTTP 403 and
  the same text (`backend/open_webui/routers/audio.py:612-616`). The button is also hidden in read-only views
  such as a shared chat, whatever the permission (`readOnly`, same line).
- **`chat.call` off:** no **Voice mode** button; the **Send message** button shows in its place
  (`src/lib/components/chat/MessageInput.svelte:2671`, `:2734-2745`). There is no separate server check for calls:
  a call is made of ordinary transcription, chat and speech requests, each checked as above. A user who has
  `chat.call` but not `chat.stt` can open a call, but every turn is refused by the transcription endpoint
  (section 5.3).
- The permission refusals use HTTP **403**, unlike the role checks elsewhere in the application, which answer
  401 (`backend/open_webui/routers/audio.py:1259-1261`; ground truth, "Role checks answer 401, not 403").

### 3.4 Attached Recordings

Transcribing an attached audio file is part of upload processing (`backend/open_webui/routers/files.py:152-165`),
so it follows the upload rules described in `files-uploads-and-storage.md` (in the chat composer, the
`chat.file_upload` permission) rather than `chat.stt`. An administrator who turns speech-to-text off to keep voice
data away from an outside service should know that attached recordings are still sent to the configured
speech-to-text engine. Whether that is intended is listed in section 14.

### 3.5 Settings That Only Administrators Can Change

Every `audio.*` setting is changed only through the admin endpoints (`get_admin_user`,
`backend/open_webui/routers/audio.py:282-323`), or by environment variables before first boot (section 7). The
**Voice Mode Prompt** that shapes answers during calls is an admin Interface setting (section 7.3). Users can
change only their personal Audio settings (section 7.2), which are stored with their own user settings.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Speech-to-text** (STT), **transcription** | Turning a recording into text. Used by dictation, voice calls and attached recordings | `backend/open_webui/routers/audio.py:1135-1188` |
| **Text-to-speech** (TTS), **speech** | Turning text into spoken audio. Used by Read Aloud and voice calls | `backend/open_webui/routers/audio.py:601-667` |
| **Engine** | The service that does the work. The administrator picks one speech-to-text engine and one text-to-speech engine for the server (`audio.stt.engine`, `audio.tts.engine`); a user can switch their own device to a browser engine (section 7.2) | `backend/open_webui/config.py:3057`, `:3073` |
| **Web API** (browser speech) | The speech services built into the web browser (the Web Speech API). In the admin list it is the value `web` for speech-to-text and the empty value for text-to-speech, so "empty" means *browser* for text-to-speech but *local Whisper* for speech-to-text | `src/lib/components/admin/Settings/Audio.svelte:264-273`, `:511-518` |
| **Whisper (Local)** | Speech recognition run on the MedIT GPT server itself with the faster-whisper library; the stored engine value is empty. The code default model is `base` | `src/lib/components/admin/Settings/Audio.svelte:265-267`; `backend/open_webui/config.py:1562`; `backend/open_webui/routers/audio.py:217-238` |
| **Whisper model** | The size or name of the local Whisper model (for example `base`). It is loaded the first time someone transcribes after a restart, and downloaded if it is not already on disk | `backend/open_webui/routers/audio.py:670-674`, `:232-237`; `backend/open_webui/main.py:776` |
| **OpenAI** (OpenAI-compatible) | Any service that offers OpenAI's `/audio/transcriptions` and `/audio/speech` interface at the configured address. The code default address is `https://api.openai.com/v1` | `backend/open_webui/routers/audio.py:417`, `:726`, `:744`; `backend/open_webui/config.py:367`, `:1580`, `:1621` |
| **Azure AI Speech** | Microsoft's speech service; region `eastus` when none is set | `backend/open_webui/routers/audio.py:482`, `:853` |
| **Deepgram** | A speech-to-text service at `https://api.deepgram.com/v1/listen` | `backend/open_webui/routers/audio.py:795` |
| **ElevenLabs** | A text-to-speech service; address from `ELEVENLABS_API_BASE_URL` (code default `https://api.elevenlabs.io`) | `backend/open_webui/config.py:1578`; `backend/open_webui/routers/audio.py:458` |
| **MistralAI** (Voxtral) | Mistral's speech services; default models `voxtral-mini-latest` (speech-to-text) and `voxtral-mini-tts-2603` (text-to-speech) | `backend/open_webui/routers/audio.py:1005`, `:567` |
| **Transformers (Local)** | Text-to-speech run on the server with Microsoft SpeechT5 and a CMU Arctic speaker voice | `backend/open_webui/routers/audio.py:326-338`, `:516-549` |
| **Kokoro.js (Browser)** | A text-to-speech model that runs inside the user's browser; chosen per user, not by the administrator | `src/lib/components/chat/Settings/Audio.svelte:254-256`; `src/lib/workers/kokoro.worker.ts:9` |
| **dtype** | Kokoro's model precision (`fp32`, `fp16`, `q8`, `q4`): smaller is lighter but lower quality | `src/lib/components/chat/Settings/Audio.svelte:264-274` |
| **Voice** | Which speaker the text-to-speech engine uses. The order of precedence is: the model's own voice, then the user's personal voice (only while the administrator's default voice is unchanged since the user saved it), then the administrator's default voice | `src/lib/components/chat/Messages/ResponseMessage.svelte:265-270`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:385-396` |
| **Response splitting** | How an answer is cut into pieces before each piece is turned into speech: `punctuation` (sentences, the default), `paragraphs`, or `none` (one piece) | `src/lib/types/index.ts:12-16`; `src/lib/utils/index.ts:1184-1210` |
| **Dictate**, **dictation bar** | The microphone in the composer and the purple recording strip it opens (cancel, a level meter, a timer, confirm) | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:464-643` |
| **Voice mode**, **call**, **call overlay** | The hands-free conversation screen | `src/lib/components/chat/MessageInput/CallOverlay.svelte:787-1146` |
| **Voice Mode Prompt** | An instruction the server adds to every message sent during a call so the model answers briefly and conversationally | `backend/open_webui/utils/middleware.py:2675-2685`; `backend/open_webui/config.py:2387-2410` |
| **Voice interruption** | A personal setting that lets the user's speech cut the assistant off mid-answer during a call | `src/lib/components/common/InterfaceSettings.svelte:1855-1874`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:323` |
| **Speech cache** | Server folder where generated speech is kept so the same text is not generated twice | `backend/open_webui/routers/audio.py:77-78`, `:619-642` |
| **Conversion**, **compression**, **chunking** | Server preparation of a recording before transcription: unusual formats become MP3, recordings over 20 MB are shrunk, and anything still over 20 MB is cut into pieces. This uses the pydub library, which relies on ffmpeg | `backend/open_webui/routers/audio.py:126-166`, `:1191-1248`; `Dockerfile:145-147` |
| **Slim image** | A smaller build of the application (`USE_SLIM`) without local models or audio conversion; outside speech services and the browser's own speech (`Web API`, Kokoro.js) work. *Corrected 2026-10-10: this row said "only outside speech services work"; in the slim build only `Whisper (Local)` and `Transformers (Local)` are greyed out and refused by the server, while `Web API` stays selectable (`src/lib/components/admin/Settings/Audio.svelte:265-269`, `:511-514`; `backend/open_webui/routers/audio.py:291-297`).* | `backend/open_webui/env.py:45`, `:857`; `src/lib/components/admin/Settings/Audio.svelte:250-256` |
| **Supported MIME types** | The list of file types the server accepts for transcription; empty means `audio/*` and `video/webm` | `backend/open_webui/utils/misc.py:1204-1208` |
| **Speech-to-text language** | A personal two-letter code (ISO-639-1, for example `en` or `fr`) sent with each recording to help the engine | `src/lib/components/chat/Settings/Audio.svelte:205-223` |

## 5. Workflows (Step by Step)

### 5.1 Dictating a Message (Dictate)

1. In the composer, the user clicks the microphone (tooltip `Dictate`). It is shown only when no answer is being
   written and the user has `chat.stt` (`src/lib/components/chat/MessageInput.svelte:2629-2631`). **Cmd+Shift+L**
   does the same (section 2.3).
2. The browser is asked for the microphone. If it refuses, a red pop-up reads
   `Permission denied when accessing microphone: {error}` (`src/lib/components/chat/MessageInput.svelte:2639-2651`).
   The test stream is closed straight away; the dictation bar then opens the microphone again with echo
   cancellation, noise suppression and automatic gain switched on
   (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:224-232`). If that second request fails, the
   pop-up reads `Error accessing media devices.` (`:233-239`).
3. The composer is replaced by the dictation bar: an **X** to cancel, a moving level meter, a `0:00` timer and a
   tick button (`Confirm recording`) (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:464-643`). The
   code asks the device to keep the screen awake while recording (`:61-87`). **Escape** cancels (`:422-428`).
4. The browser records in the first format it supports from this list: `audio/webm; codecs=opus`, `audio/webm`,
   `audio/ogg; codecs=opus`, `audio/mp4`, `audio/wav` (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:241-251`).
   If recording cannot start, the pop-up reads `Error starting recording.` (`:290-297`).
5. **Server engine** (anything except `Web API`): the user clicks the tick. The bar shows a spinner while the file,
   named `Recording-{date and time}.{ext}`, is sent to `POST /api/v1/audio/transcriptions` together with the user's
   speech-to-text language if one is set (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:174-198`;
   `src/lib/apis/audio/index.ts:67-98`). The server's processing is in section 5.9.
6. **Browser engine** (`Web API`, chosen by the administrator or by the user, section 7.2): the browser's own speech
   recognition listens while the bar is open. Recognition ends by itself about two seconds after the last
   recognised words, and the text is inserted without waiting for the tick
   (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:300-351`). The code does not set a recognition
   language, so the browser chooses one. A browser that has no speech recognition records but produces no text,
   and nothing is inserted (`:181-184`, `:302`). A recognition failure shows `Speech recognition error: {error}`
   and closes the bar (`:354-360`).
7. The text is inserted at the cursor. When **Instant Auto-Send After Voice Transcription** is on, the message is
   sent at once (`src/lib/components/chat/MessageInput.svelte:1744-1757`).
8. If the server refuses or fails, the server's message is shown as a red pop-up and nothing is inserted
   (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:186-193`). If the failure does not come back as a
   normal server error (for example the server cannot be reached, or something in front of it rejects the
   upload), the bar simply closes and no message appears (`src/lib/apis/audio/index.ts:83-97`: the error text is
   read from the response, and when there is none the call returns nothing).

The channel composer, the notes editor and the knowledge-base text window use the same bar
(`src/lib/components/channel/MessageInput.svelte:776`; `src/lib/components/notes/NoteEditor.svelte:1473`;
`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:82`).

### 5.2 Listening to an Answer (Read Aloud)

1. Under an answer, the user clicks the speaker (tooltip `Read Aloud`). It is shown for users with `chat.tts`, and
   not in read-only views (`src/lib/components/chat/Messages/ResponseMessage.svelte:1146-1160`). While speech is
   being prepared the icon is three dots; while speaking, a crossed speaker; clicking it then stops the speech
   (`:1154-1160`, `:1163-1229`).
2. The text spoken is the visible answer, with collapsible sections (reasoning, tool output) removed
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:203-204`, `:273`). If there is nothing left, the
   message is `No content to speak` (`:274-277`).
3. **Browser speech** (administrator text-to-speech engine `Web API`): the whole answer is handed to the browser's
   speech synthesis in one piece, at the user's playback speed, with the chosen voice when the browser has a voice
   whose identifier matches (`src/lib/components/chat/Messages/ResponseMessage.svelte:285-309`). The code waits for
   the browser to report its voices; until it does, nothing is spoken (`:287-290`). The personal Kokoro choice is
   not used on this path.
4. **Server engine or Kokoro**: the answer is cleaned (code blocks, tables, emoji and Markdown symbols are
   removed) and split according to **Response Splitting** (`src/lib/utils/index.ts:1012-1055`, `:1184-1210`); short
   sentences are joined to the next one until a piece has at least four words and fifty characters
   (`src/lib/utils/index.ts:1165-1182`).
   - With **Kokoro.js (Browser)** as the personal engine, each piece is generated in the browser
     (`src/lib/components/chat/Messages/ResponseMessage.svelte:334-363`).
   - Otherwise each piece is sent in turn to `POST /api/v1/audio/speech` with the voice from section 4
     (`src/lib/components/chat/Messages/ResponseMessage.svelte:364-385`; `src/lib/apis/audio/index.ts:100-136`).
   - Pieces play one after another in a hidden audio player at the personal playback speed
     (`src/lib/utils/audio.ts:10-88`; `src/lib/components/chat/Chat.svelte:1563-1564`, `:4177`).
5. A failure shows the server's message as a red pop-up. The loop goes on to the remaining pieces, so a failing
   service can produce one identical pop-up per sentence; nothing more is played for that answer
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:365-385`). When the failure carries no message (as in
   step 8 of section 5.1), no pop-up appears and the button keeps showing the three dots; it ignores clicks while
   it does (`src/lib/components/chat/Messages/ResponseMessage.svelte:1155-1161`).
6. **Auto-Playback Response**: when this personal setting is on and no call is open, the code clicks the new
   answer's Read Aloud button as soon as the answer finishes (`src/lib/components/chat/Chat.svelte:2864-2867`).

### 5.3 Holding a Voice Call (Voice Mode)

1. The **Voice mode** button appears when the text box is empty, nothing is attached, the composer is not embedded
   in another screen, and the user has `chat.call` (`src/lib/components/chat/MessageInput.svelte:2671`).
2. On click the code checks, in order (`src/lib/components/chat/MessageInput.svelte:2678-2727`):
   - no more than one model is selected, otherwise `Select only one model to call` (*Corrected 2026-10-10: this
     said "exactly one"; the code tests only for more than one, `selectedModels.length > 1`,
     `src/lib/components/chat/MessageInput.svelte:2679`*);
   - the administrator's speech-to-text engine is not `Web API`, otherwise
     `Call feature is not supported when using Web STT engine`;
   - the microphone can be opened, otherwise `Permission denied when accessing media devices`;
   - if the user's personal engine is Kokoro, the Kokoro model is loaded first (this can take a while on first use,
     section 5.6).
3. The call screen opens in the side panel (`src/lib/components/chat/ChatControls.svelte:196-216`, `:328-339`). It
   asks the device to keep the screen awake (`src/lib/components/chat/MessageInput/CallOverlay.svelte:707-734`) and
   opens the microphone with echo cancellation, noise suppression and gain control (`:233-243`).
4. **Listening...** The code waits for sound. When it hears anything, it starts recording and, if the assistant is
   still answering, stops the answer and its speech. When it has heard two seconds of silence it stops recording
   and sends the turn (`src/lib/components/chat/MessageInput/CallOverlay.svelte:317-376`, `:477-496`).
5. **Thinking...** Each turn is uploaded as `recording.wav` to `POST /api/v1/audio/transcriptions` with the user's
   language. Turns smaller than 100 bytes are dropped. If the text is not empty it is sent as an ordinary chat
   message; when the camera is on, a still from the camera goes with it
   (`src/lib/components/chat/MessageInput/CallOverlay.svelte:157-184`, `:200-220`). A transcription error appears
   as a red pop-up (`:171-174`).
6. The chat request carries a "voice" flag, and the server adds the **Voice Mode Prompt** so the answer is short and
   conversational (`src/lib/components/chat/Chat.svelte:3396-3398`; `backend/open_webui/utils/middleware.py:2675-2685`).
7. **Tap to interrupt.** As the answer streams in, each finished sentence is turned into speech (server engine,
   Kokoro, or the browser when the administrator engine is `Web API`) and played in order
   (`src/lib/components/chat/Chat.svelte:1910-1946`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:504-610`).
   While the assistant speaks, the microphone is ignored unless the personal setting **Allow Voice Interruption in
   Call** is on (`src/lib/components/chat/MessageInput/CallOverlay.svelte:323-340`). Tapping the status line or the
   picture stops the assistant (`:867-873`, `:976-984`).
8. **Controls** (`src/lib/components/chat/MessageInput/CallOverlay.svelte:998-1143`): **Camera** (asks for the camera
   and shows a live view; a switch menu lists the cameras and, where the browser supports it, `Screen Share`; the
   choice is remembered in the browser); **Mute** / **Unmute**, also the **M** key, which throws away a half-spoken
   turn and is switched off again automatically when the assistant next finishes speaking (`:666-690`); **End call**
   (the X), which stops the microphone and camera and closes the screen.
9. With **Display Emoji in Call** on, each sentence also gets an emoji generated by a separate model request, shown
   instead of the model picture (`src/lib/components/chat/MessageInput/CallOverlay.svelte:504-518`, `:570-574`).

Points that matter for support:

- A speech failure during a call shows **no** pop-up (`src/lib/components/chat/MessageInput/CallOverlay.svelte:534-540`).
  The sentence never becomes playable, so the call waits on it, shows `Tap to interrupt` and, without voice
  interruption, ignores the microphone (`:594-598`, `:323-340`). Tapping the status line recovers (`:976-984`).
- Any sound, including background noise, counts as speech: in a noisy room a turn may never end, and, when **Allow
  Voice Interruption in Call** is on, noise heard while an answer is still being written stops that answer (`src/lib/components/chat/MessageInput/CallOverlay.svelte:343-357`, `:481-483`).
  *Corrected 2026-10-10: the sentence did not say this needs voice interruption. With that setting off (the
  default) the microphone is ignored from the start of the answer until it has been spoken (`:323-340`,
  `:612-629`); noise picked up before the answer starts is recorded as an extra turn, which is sent as a new
  message if it transcribes to any text (section 11.11).*
- Each turn is labelled WAV whatever the browser actually recorded (`src/lib/components/chat/MessageInput/CallOverlay.svelte:215`, `:249`);
  the server checks the real format and converts it when it can (section 5.9).

### 5.4 Transcribing an Attached Recording

1. The user attaches an audio file (or a video) in the composer. When they have a speech-to-text language set, it
   is sent with the upload (`src/lib/components/chat/MessageInput.svelte:1002-1016`).
2. The server stores the file, and its background processing checks the file type against the **Supported MIME
   Types** list (empty means `audio/*` and `video/webm`) (`backend/open_webui/routers/files.py:146-152`;
   `backend/open_webui/utils/misc.py:1204-1208`).
3. A match is transcribed exactly as in section 5.9 and the transcript becomes the file's text for the model and for
   search (`backend/open_webui/routers/files.py:152-165`).
4. A failure marks the file as failed with the error text (`backend/open_webui/routers/files.py:258-268`). Upload
   limits, the progress chip and the failure messages are in `files-uploads-and-storage.md`.

The **Allowed extensions** list (`audio.stt.allowed_extensions`) is checked only by the transcription endpoint, not
by uploads (`backend/open_webui/routers/audio.py:1276-1281`).

### 5.5 Choosing Personal Audio Settings

1. **Settings > Audio**. Under **STT Settings**: **Speech-to-Text Engine** (`Default` or `Web API`) and **Language**
   (both hidden when the administrator's engine is already `Web API`), and **Instant Auto-Send After Voice
   Transcription** (`src/lib/components/chat/Settings/Audio.svelte:189-242`).
2. Under **TTS Settings**: **Text-to-Speech Engine** (`Default` or `Kokoro.js (Browser)`), **Kokoro.js Dtype** for
   Kokoro, **Auto-Playback Response**, and **Speech Playback Speed** (a number, `1` is normal)
   (`src/lib/components/chat/Settings/Audio.svelte:244-307`).
3. Under **Voice**: for Kokoro, a voice list once the model has loaded; for the browser engine, the browser's voices
   with **Allow non-local voices**; for a server engine, the voices the server reports
   (`src/lib/components/chat/Settings/Audio.svelte:309-398`).
4. The two switches save as soon as they are flipped; everything else needs **Save**, which shows
   `Settings saved successfully!` (`src/lib/components/chat/Settings/Audio.svelte:81-89`, `:161-182`;
   `src/lib/components/chat/SettingsModal.svelte:832-838`). The settings are stored on the server with the user's
   account, so they follow the user to other devices (`src/lib/components/chat/SettingsModal.svelte:438-451`;
   `backend/open_webui/models/users.py:171`).
5. Two call options live on the **Interface** tab under **Voice**: **Allow Voice Interruption in Call** and
   **Display Emoji in Call** (`src/lib/components/common/InterfaceSettings.svelte:1851-1897`).

### 5.6 Loading Kokoro in the Browser

1. Choosing **Kokoro.js (Browser)** and a dtype in Settings > Audio loads the model `onnx-community/Kokoro-82M-v1.0-ONNX`
   into the page, showing `Loading Kokoro.js...` with a percentage and
   `Please do not close the settings page while loading the model.`
   (`src/lib/components/chat/Settings/Audio.svelte:124-158`, `:331-347`).
2. The model runs on the graphics card through WebGPU when the browser offers it, otherwise in WebAssembly
   (`src/lib/workers/kokoro.worker.ts:21-24`). For speaking, a separate background worker loads the model again the
   first time Read Aloud or a call needs it (`src/lib/workers/KokoroWorker.ts:19-71`;
   `src/lib/components/chat/Messages/ResponseMessage.svelte:334-343`).
3. Text never leaves the browser on this path. The model files are downloaded by the browser; the repository does
   not set where from, so the library default applies (section 14).

### 5.7 Choosing the Server Speech-to-Text Engine (Administrator)

1. **Admin Panel > Settings > Audio**, section **Speech-to-Text**, **Speech-to-Text Engine**: `Whisper (Local)`,
   `OpenAI`, `Web API`, `Deepgram`, `Azure AI Speech`, `MistralAI`
   (`src/lib/components/admin/Settings/Audio.svelte:259-274`).
2. Fill in the engine's fields (section 7.1) and click **Save**; success shows `Settings saved successfully!`
   (`src/lib/components/admin/Settings/Audio.svelte:136-186`, `:733-740`; `src/lib/components/chat/SettingsModal.svelte:885-890`).
3. **Whisper (Local):** type a model name (code default `base`) and either click the download button
   (`Update model`) or **Save**. Either way the server loads the model during the save, downloading it into the
   Whisper model folder if needed, so the save can take a long time
   (`src/lib/components/admin/Settings/Audio.svelte:188-192`, `:431-480`; `backend/open_webui/routers/audio.py:305-308`, `:217-238`).
   Choosing any other engine unloads the local model (`backend/open_webui/routers/audio.py:309-310`).
4. **Web API:** recognition moves to each user's browser; the server is not involved, voice calls are refused
   (section 5.3) and the Supported MIME Types field is hidden (`src/lib/components/admin/Settings/Audio.svelte:276-287`).

### 5.8 Choosing the Server Text-to-Speech Engine and Voice (Administrator)

1. Same page, section **Text-to-Speech**, **Text-to-Speech Engine**: `Web API`, `Transformers (Local)`, `OpenAI`,
   `ElevenLabs`, `Azure AI Speech`, `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:484-519`).
2. **Changing this list saves the whole Audio page immediately**, without **Save**, and resets the voice and model:
   OpenAI to `alloy` and `tts-1`, MistralAI to no voice and `voxtral-mini-tts-2603`, the others to empty
   (`src/lib/components/admin/Settings/Audio.svelte:492-509`).
3. Fill in the engine's fields, choose a **TTS Voice** (and a model where offered); the voice and model lists come
   from the engine (`GET /api/v1/audio/voices`, `GET /api/v1/audio/models`) (`src/lib/components/admin/Settings/Audio.svelte:88-134`, `:595-716`).
   For `Web API`, the voice list is the administrator's own browser's voices, which other users' devices may not have.
4. Choose **Response Splitting** and click **Save** (`src/lib/components/admin/Settings/Audio.svelte:718-740`).
5. Changing the default voice makes every user's personal voice choice stop applying until that user saves their
   Audio settings again (`src/lib/components/chat/Settings/Audio.svelte:103-107`, `:176`;
   `src/lib/components/chat/Messages/ResponseMessage.svelte:265-270`).

### 5.9 What the Server Does With a Recording

`transcribe()` in `backend/open_webui/routers/audio.py:1135-1188`, used by both dictation and attached files:

1. The transcription endpoint checks `chat.stt`, the file type against **Supported MIME Types**, and the extension
   against `audio.stt.allowed_extensions` (code default `mp3,wav,m4a,webm,ogg,flac,mp4,mpga,mpeg`), then saves the
   upload as `{random id}.{ext}` in `DATA_DIR/cache/audio/transcriptions/`
   (`backend/open_webui/routers/audio.py:1258-1297`; `backend/open_webui/config.py:1596-1603`).
2. Unless `BYPASS_PYDUB_PREPROCESSING` is on (always on in the slim image), the server reads the audio codec
   name from the file and converts the file to MP3 unless that name is one of `flac`, `m4a`, `mp3`, `mp4`,
   `mpeg`, `wav` or `webm`; AAC audio is always converted. If the format cannot be read at all (for example
   because the ffmpeg tools are missing), the file is sent on unconverted. A failed conversion stops with
   `Audio conversion failed. The audio file may be corrupted or empty.`
   (`backend/open_webui/routers/audio.py:126-153`, `:156-166`, `:1138-1148`; `backend/open_webui/env.py:857`).
3. A file over 20 MB is re-encoded as 16 kHz mono MP3 at 32 kbit/s, and anything still over 20 MB is cut into
   pieces of at most 20 MB, transcribed together and joined with spaces (`backend/open_webui/routers/audio.py:72-73`,
   `:1150-1169`, `:1186-1248`). A failure here stops with `[ERROR: Error processing audio file]` (or a storage
   error, section 10).
4. The language sent is the server-wide `WHISPER_LANGUAGE` when set, otherwise the user's language
   (`backend/open_webui/routers/audio.py:969-972`). How each engine uses it:

| Engine (`audio.stt.engine`) | Language handling | Other behaviour | Source |
|---|---|---|---|
| empty (Whisper, local) | Uses the language, or detects it when none is given; no retry | Loads the model on first use after a restart; beam size 5; voice-activity filter and multilingual mode from `WHISPER_VAD_FILTER`, `WHISPER_MULTILINGUAL` | `backend/open_webui/routers/audio.py:670-696` |
| `openai` | Tries with the language, and if that fails, once more without it | Sends the file as a multipart upload, or as base64 JSON when **Request Format** is `JSON Base64` | `backend/open_webui/routers/audio.py:699-771` |
| `deepgram` | As OpenAI | `smart_format` on; the model is optional | `backend/open_webui/routers/audio.py:774-837` |
| `azure` | Ignores the user's language; uses **Language Locales**, or 13 common locales when empty | Speaker separation for up to **Max Speakers** (default 3); 200 MB per file | `backend/open_webui/routers/audio.py:840-959` |
| `mistral` | Uses the user's language only (not `WHISPER_LANGUAGE`) | Either the transcription interface or, with **Use Chat Completions API**, a chat request asking for a word-for-word transcript; 20 MB per file | `backend/open_webui/routers/audio.py:987-1132` |
| `web` | Not handled by the server | An attached recording fails with this engine, because no server engine is selected | `backend/open_webui/routers/audio.py:974-984`, `:1186-1188` |

5. Each piece's transcript is saved as `{id}.json` next to the piece; temporary pieces are deleted afterwards, the
   original upload, any converted copy and the transcripts are not (`backend/open_webui/routers/audio.py:692-693`,
   `:1177-1184`; section 6).
6. The endpoint answers with the text and the stored file name, and publishes an `audio.transcription_requested`
   event (section 9) (`backend/open_webui/routers/audio.py:1305-1321`).

### 5.10 What the Server Does With a Speech Request

`POST /api/v1/audio/speech` (`backend/open_webui/routers/audio.py:601-667`):

1. If the engine is empty (`Web API`) the answer is HTTP 404 `We could not find what you're looking for :/`: the
   browser is meant to speak (`:606-610`). In the slim image an empty or `transformers` engine gives
   `Configure an external text-to-speech engine.` (`:604-605`).
2. Users without `chat.tts` are refused (section 3).
3. The request is identified by a fingerprint of its text and voice plus the engine and model. If that speech is
   already cached it is returned at once (`:618-642`).
4. Otherwise the engine handler runs (`:650-654`):

| Engine (`audio.tts.engine`) | What the server sends | Notes | Source |
|---|---|---|---|
| `openai` | The text, the voice (or the default voice), the configured model, plus **Additional Parameters** | Non-MP3 audio returned by the service (for example raw PCM) is converted to MP3 | `backend/open_webui/routers/audio.py:397-441`, `:169-214` |
| `elevenlabs` | The text and model to `{ELEVENLABS_API_BASE_URL}/v1/text-to-speech/{voice}` | Refuses an empty or unknown voice with `Invalid voice id` | `backend/open_webui/routers/audio.py:444-477` |
| `azure` | SSML with the voice name; the language is taken from the first two parts of the voice name (for example `en-US`) | Output format from `audio.tts.azure.speech_output_format` | `backend/open_webui/routers/audio.py:480-513` |
| `transformers` | Nothing leaves the server: SpeechT5 on the server, speaker chosen by the model field (a CMU Arctic name), with a fixed fallback speaker | Downloads the SpeechT5 model and speaker set on first use | `backend/open_webui/routers/audio.py:516-549`, `:326-338` |
| `mistral` | The text, voice and model, asking for MP3 | Needs the Mistral key | `backend/open_webui/routers/audio.py:552-588` |

5. The audio and a copy of the request (including the text) are saved in the speech cache, and an
   `audio.speech_requested` event is published (`backend/open_webui/routers/audio.py:363-394`, `:655-666`).

## 6. Data Model

There is **no database table for audio**. Speech features keep their state in four places: persistent settings,
user and model JSON fields, files under `DATA_DIR`, and the browser.

### 6.1 Database Fields

| What | Where | Shape | Source |
|---|---|---|---|
| Server engines, addresses, keys, voice, model, splitting, file-type lists | `config` table, one row per `audio.*` key (30 keys) | See section 7.1 | `backend/open_webui/config.py:3052-3081`; `backend/open_webui/models/config.py:101-108` |
| Voice Mode Prompt switch and text | `config` rows `task.voice.prompt.enable`, `task.voice.prompt_template` | Boolean; text | `backend/open_webui/config.py:3152-3153` |
| Default speech permissions | `config` row `user.permissions`, keys `chat.stt`, `chat.tts`, `chat.call` | Booleans | `backend/open_webui/config.py:1994-1996` |
| Group speech permissions | `group.permissions` JSON, same keys | Booleans | `backend/open_webui/models/groups.py:49` |
| A user's personal audio choices | `user.settings` JSON, under `ui` | `audio.stt.engine`, `audio.stt.language`, `audio.tts.engine`, `audio.tts.engineConfig.dtype`, `audio.tts.playbackRate`, `audio.tts.voice`, `audio.tts.defaultVoice`, `audio.tts.nonLocalVoices`, plus `speechAutoSend`, `responseAutoPlayback`, `voiceInterruption`, `showEmojiInCall` | `backend/open_webui/models/users.py:138-141`, `:171`; `src/lib/components/chat/Settings/Audio.svelte:81-89`, `:165-180`; `src/lib/stores/index.ts:228-229`, `:270-273`, `:309-317` |
| A model's own voice | `model.meta` JSON, `tts.voice` | Text (voice id) | `backend/open_webui/models/models.py:121`; `src/lib/components/workspace/Models/ModelEditor.svelte:414-423` |

`audio.tts.defaultVoice` in the user's settings records the administrator's default voice at the moment the user
saved; it is how the code decides whether the user's own voice still applies (section 5.8, step 5).

The settings type also lists `conversationMode` (after browser speech, start dictation again), but no screen in
this version sets it; only older saved settings can contain it (`src/lib/stores/index.ts:270`;
`src/lib/components/chat/Settings/Audio.svelte:22`, `:93`; `src/lib/components/chat/Messages/ResponseMessage.svelte:298-300`).

### 6.2 Files on the Server

All paths are under `DATA_DIR` (`backend/data` outside Docker, `/app/backend/data` in the image; ground truth). The
cache folder is `DATA_DIR/cache` (`backend/open_webui/config.py:182`).

| Folder | What is written | When | Holds personal data? | Source |
|---|---|---|---|---|
| `cache/audio/speech/` | `{fingerprint}.mp3` (the generated speech) and `{fingerprint}.json` (the request: the text that was spoken, the voice and, for OpenAI, the model and extra parameters); in the slim image also `{fingerprint}.mime` | Each first-time Read Aloud or call sentence with a server engine | **Yes**: the `.json` holds the answer text and the audio speaks it | `backend/open_webui/routers/audio.py:77-78`, `:363-394`, `:619-627`, `:435-436` |
| `cache/audio/transcriptions/` | `{id}.{ext}` (the user's recording), `{id}.mp3` when converted, `{id}_compressed.mp3` when over 20 MB, and `{id}.json` or `{id}_chunk_{n}.json` (the transcript) | Each dictation and each call turn with a server engine | **Yes**: voice recordings and their transcripts | `backend/open_webui/routers/audio.py:1283-1297`, `:156-166`, `:1191-1205`, `:692-693` |
| `uploads/` | Beside an attached recording: the converted `.mp3`, a compressed copy, and the transcript `.json` | Upload processing of an audio attachment | **Yes** | `backend/open_webui/routers/files.py:152-158`; `backend/open_webui/routers/audio.py:962-965` |
| `cache/whisper/models/` | Downloaded local Whisper models (folder set by `WHISPER_MODEL_DIR`) | First use or **Update model** | No | `backend/open_webui/config.py:1565`; `Dockerfile:97-99` |
| Hugging Face cache | SpeechT5 and the CMU Arctic speaker set for `Transformers (Local)` | First local text-to-speech request | No | `backend/open_webui/routers/audio.py:326-338`; `Dockerfile:111-112` |

**Fingerprint.** Speech files are named by a SHA-256 fingerprint of the request body (text and voice) plus the
engine and model, so the same sentence in the same voice is generated once and then served from the cache to any
user who asks for it (`backend/open_webui/routers/audio.py:618-642`). A change of engine or model gives new
fingerprints; a change of voice changes the request body and therefore the fingerprint.

**Retention.** The code never deletes these files. The transcription endpoint removes only the temporary pieces
it cut, "never the original file" (`backend/open_webui/routers/audio.py:1177-1184`); deleting an uploaded file
removes only the stored original, not the converted copy or transcript beside it
(`backend/open_webui/storage/provider.py:79-86`); deleting a chat or a user does not touch the cache (no reference to
these folders outside the audio router, `backend/open_webui/routers/audio.py:77`, `:1288`). There is no background
clean-up (section 8). How long production keeps them, whether they are backed up, and who may clear them is
**TO BE CONFIRMED**. Because MedIT GPT chats may contain health information, these folders must be treated like the
database: tier 1 never opens them.

Who can retrieve files from the server cache is a security question: **Security-sensitive: refer to the platform
maintainer and U of T Information Security (security.utoronto.ca).**

### 6.3 Data Kept in the Browser

| What | Where | Source |
|---|---|---|
| The camera chosen in a call | Browser `localStorage`, `selectedVideoInputDeviceId` | `src/lib/components/chat/MessageInput/CallOverlay.svelte:67-72`, `:1005` |
| Kokoro model files | Downloaded by the browser; whether they are cached between visits is decided by the library (**TO BE CONFIRMED**) | `src/lib/workers/kokoro.worker.ts:9`, `:21-24` |
| Generated speech while it plays | Temporary in-page addresses (`blob:`), released with the page | `src/lib/components/chat/Messages/ResponseMessage.svelte:380-382`; `src/lib/workers/kokoro.worker.ts:45-47` |

### 6.4 Data Sent Outside MedIT GPT

| Engine | What leaves the server | Destination | Source |
|---|---|---|---|
| `openai` (speech-to-text) | The recording, the model name, the language | `{audio.stt.openai.api_base_url}/audio/transcriptions` | `backend/open_webui/routers/audio.py:699-748` |
| `deepgram` | The recording and language | `https://api.deepgram.com/v1/listen` | `backend/open_webui/routers/audio.py:787-800` |
| `azure` (speech-to-text) | The recording and the locale list | `{audio.stt.azure.base_url}` or `https://{region}.api.cognitive.microsoft.com` | `backend/open_webui/routers/audio.py:882-908` |
| `mistral` (speech-to-text) | The recording (base64 inside a chat request in chat mode) and language | `{audio.stt.mistral.api_base_url}`, default `https://api.mistral.ai/v1` | `backend/open_webui/routers/audio.py:997`, `:1045-1063`, `:1077-1096` |
| `openai` (text-to-speech) | The answer text, voice, model | `{audio.tts.openai.api_base_url}/audio/speech` | `backend/open_webui/routers/audio.py:397-421` |
| `elevenlabs` | The answer text, model, voice | `{ELEVENLABS_API_BASE_URL}/v1/text-to-speech/{voice}` | `backend/open_webui/routers/audio.py:457-470` |
| `azure` (text-to-speech) | The answer text inside SSML | `{audio.tts.azure.speech_base_url}` or `https://{region}.tts.speech.microsoft.com` | `backend/open_webui/routers/audio.py:488-506` |
| `mistral` (text-to-speech) | The answer text, voice, model | `{audio.tts.mistral.api_base_url}/audio/speech` | `backend/open_webui/routers/audio.py:563-576` |
| Browser speech (`Web API`) | Whatever the browser's own speech service does; outside MedIT GPT's control | The browser vendor's service, if any (**TO BE CONFIRMED** per browser) | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:300-317`; `src/lib/components/chat/Messages/ResponseMessage.svelte:285-309` |

When `ENABLE_FORWARD_USER_INFO_HEADERS` is on, OpenAI-compatible speech requests also carry the signed-in user's
details in request headers (`backend/open_webui/routers/audio.py:410-411`, `:709-710`;
`backend/open_webui/env.py:989`). Local Whisper, `Transformers (Local)` and Kokoro send no audio or text out of
MedIT GPT once their models are downloaded.

## 7. Settings and Configuration

Code defaults below are what the repository says. **Live values are data in the `config` table (or the environment)
and are TO BE CONFIRMED for production.** After first boot the stored value wins and changing the environment
variable has no effect (ground truth, "Settings: Where a Value Comes From"). Keys and secrets are cited by location
only. The full persistent-settings catalogue is in `configuration-persistent-settings-a-to-o.md`.

### 7.1 Server Settings (`audio.*`, Admin Panel > Settings > Audio)

All 30 keys are seeded in `DEFAULT_CONFIG` (`backend/open_webui/config.py:3052-3081`) from the variables defined at
`backend/open_webui/config.py:1561-1654`, and read or written by `backend/open_webui/routers/audio.py:80-114`.
Admin labels are dotted keys resolved in `src/lib/i18n/locales/en-US/translation.json:1977-2021`.

**Speech-to-text (17 keys)**

| Key | Environment variable | Code default | Admin label (shown when) | Effect | Source |
|---|---|---|---|---|---|
| `audio.stt.engine` | `AUDIO_STT_ENGINE` | empty = `Whisper (Local)` | **Speech-to-Text Engine** | Which engine transcribes; `web` hands dictation to the browser and blocks calls | `backend/open_webui/config.py:1586`; `src/lib/components/admin/Settings/Audio.svelte:260-274` |
| `audio.stt.whisper_model` | `WHISPER_MODEL` | `base` | **STT Model** (Whisper) with **Update model** | Local Whisper model name | `backend/open_webui/config.py:1562`; `src/lib/components/admin/Settings/Audio.svelte:435-480` |
| `audio.stt.model` | `AUDIO_STT_MODEL` | empty | **STT Model** (OpenAI, Deepgram, MistralAI) | Model name sent to the service; MistralAI falls back to `voxtral-mini-latest` | `backend/open_webui/config.py:1588`; `src/lib/components/admin/Settings/Audio.svelte:318-328`, `:338-352`, `:412-422` |
| `audio.stt.supported_content_types` | `AUDIO_STT_SUPPORTED_CONTENT_TYPES` (comma list) | empty = `audio/*`, `video/webm` | **Supported MIME Types** (any engine but `Web API`) | Which file types are transcribed, for dictation and for attachments | `backend/open_webui/config.py:1590-1594`; `src/lib/components/admin/Settings/Audio.svelte:276-287`; `backend/open_webui/utils/misc.py:1204-1208` |
| `audio.stt.allowed_extensions` | `AUDIO_STT_ALLOWED_EXTENSIONS` (comma list) | `mp3,wav,m4a,webm,ogg,flac,mp4,mpga,mpeg` | Not on the page | File-name extensions the transcription endpoint accepts; the admin page neither shows nor sends it, so it keeps its seeded value | `backend/open_webui/config.py:1596-1603`; `backend/open_webui/routers/audio.py:1276-1281`; `src/lib/components/admin/Settings/Audio.svelte:162-179` |
| `audio.stt.openai.api_base_url` | `AUDIO_STT_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **API Base URL** (OpenAI) | Service address | `backend/open_webui/config.py:1580`, `:367` |
| `audio.stt.openai.api_key` | `AUDIO_STT_OPENAI_API_KEY` | The OpenAI connection's key from the environment, if any | **API Key** (OpenAI) | Secret; location only | `backend/open_webui/config.py:1582`, `:361-366` |
| `audio.stt.openai.api_request_format` | `AUDIO_STT_OPENAI_API_REQUEST_FORMAT` | `multipart` | **Request Format**: `Multipart Upload` or `JSON Base64` | How the recording is sent | `backend/open_webui/config.py:1584`; `src/lib/components/admin/Settings/Audio.svelte:308-316` |
| `audio.stt.deepgram.api_key` | `DEEPGRAM_API_KEY` | empty | **API Key** (Deepgram) | Secret | `backend/open_webui/config.py:1575` |
| `audio.stt.azure.api_key` | `AUDIO_STT_AZURE_API_KEY` | empty | **API Key** (Azure) | Secret; required | `backend/open_webui/config.py:1605`; `backend/open_webui/routers/audio.py:878-879` |
| `audio.stt.azure.region` | `AUDIO_STT_AZURE_REGION` | empty = `eastus` | **Azure Region** | Service region | `backend/open_webui/config.py:1607`; `backend/open_webui/routers/audio.py:853` |
| `audio.stt.azure.locales` | `AUDIO_STT_AZURE_LOCALES` | empty = 13 built-in locales | **Language Locales** | Languages Azure listens for | `backend/open_webui/config.py:1609`; `backend/open_webui/routers/audio.py:858-876` |
| `audio.stt.azure.base_url` | `AUDIO_STT_AZURE_BASE_URL` | empty = the regional public address | **Endpoint URL** | Alternative address | `backend/open_webui/config.py:1611`; `backend/open_webui/routers/audio.py:887-889` |
| `audio.stt.azure.max_speakers` | `AUDIO_STT_AZURE_MAX_SPEAKERS` | empty = 3 | **Max Speakers** | Speaker separation | `backend/open_webui/config.py:1613`; `backend/open_webui/routers/audio.py:856` |
| `audio.stt.mistral.api_key` | `AUDIO_STT_MISTRAL_API_KEY` | empty | **API Key** (MistralAI) | Secret; required | `backend/open_webui/config.py:1615`; `backend/open_webui/routers/audio.py:1000-1001` |
| `audio.stt.mistral.api_base_url` | `AUDIO_STT_MISTRAL_API_BASE_URL` | `https://api.mistral.ai/v1` | **API Base URL** (MistralAI) | Service address | `backend/open_webui/config.py:1617` |
| `audio.stt.mistral.use_chat_completions` | `AUDIO_STT_MISTRAL_USE_CHAT_COMPLETIONS` | off | **Use Chat Completions API** | Transcribe through a chat request instead | `backend/open_webui/config.py:1619`; `src/lib/components/admin/Settings/Audio.svelte:424-430` |

**Text-to-speech (13 keys)**

| Key | Environment variable | Code default | Admin label (shown when) | Effect | Source |
|---|---|---|---|---|---|
| `audio.tts.engine` | `AUDIO_TTS_ENGINE` | empty = `Web API` (browser) | **Text-to-Speech Engine** (saves on change) | Which engine speaks | `backend/open_webui/config.py:1635`; `src/lib/components/admin/Settings/Audio.svelte:485-519` |
| `audio.tts.voice` | `AUDIO_TTS_VOICE` | `alloy` | **TTS Voice** | Default voice for everyone | `backend/open_webui/config.py:1640`; `src/lib/components/admin/Settings/Audio.svelte:595-607`, `:636-693` |
| `audio.tts.model` | `AUDIO_TTS_MODEL` | `tts-1` | **TTS Model** | Model for OpenAI, ElevenLabs, MistralAI; speaker name for `Transformers (Local)` | `backend/open_webui/config.py:1638`; `backend/open_webui/routers/audio.py:399`, `:461`, `:526-532`, `:567` |
| `audio.tts.split_on` | `AUDIO_TTS_SPLIT_ON` | `punctuation` | **Response Splitting** | How answers are cut before speaking | `backend/open_webui/config.py:1642`; `src/lib/components/admin/Settings/Audio.svelte:718-730` |
| `audio.tts.api_key` | `AUDIO_TTS_API_KEY` | empty | **API Key** (ElevenLabs, Azure) | Secret | `backend/open_webui/config.py:1633` |
| `audio.tts.openai.api_base_url` | `AUDIO_TTS_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **API Base URL** (OpenAI) | Service address; voice and model lists are asked of it unless it is OpenAI's own | `backend/open_webui/config.py:1621`; `backend/open_webui/routers/audio.py:1350-1378`, `:1424-1440` |
| `audio.tts.openai.api_key` | `AUDIO_TTS_OPENAI_API_KEY` | The OpenAI connection's key from the environment, if any | **API Key** (OpenAI) | Secret | `backend/open_webui/config.py:1622` |
| `audio.tts.openai.params` | `AUDIO_TTS_OPENAI_PARAMS` (JSON) | `{}` | **Additional Parameters** (OpenAI) | Extra fields merged into every OpenAI speech request | `backend/open_webui/config.py:1624-1630`; `backend/open_webui/routers/audio.py:402`; `src/lib/components/admin/Settings/Audio.svelte:655-664` |
| `audio.tts.azure.speech_region` | `AUDIO_TTS_AZURE_SPEECH_REGION` | empty = `eastus` for speech | **Azure Region** | Service region | `backend/open_webui/config.py:1644`; `backend/open_webui/routers/audio.py:482` |
| `audio.tts.azure.speech_base_url` | `AUDIO_TTS_AZURE_SPEECH_BASE_URL` | empty = the regional public address | **Endpoint URL** | Alternative address | `backend/open_webui/config.py:1646`; `backend/open_webui/routers/audio.py:498` |
| `audio.tts.azure.speech_output_format` | `AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT` | `audio-24khz-160kbitrate-mono-mp3` | **Output format** | Audio format Azure returns | `backend/open_webui/config.py:1648-1650` |
| `audio.tts.mistral.api_key` | `AUDIO_TTS_MISTRAL_API_KEY` | empty | **API Key** (MistralAI) | Secret; required | `backend/open_webui/config.py:1652`; `backend/open_webui/routers/audio.py:557-558` |
| `audio.tts.mistral.api_base_url` | `AUDIO_TTS_MISTRAL_API_BASE_URL` | `https://api.mistral.ai/v1` | **API Base URL** (MistralAI) | Service address | `backend/open_webui/config.py:1654` |

What the browser learns: signed-in users and administrators receive only `audio.tts.engine`, `audio.tts.voice`,
`audio.tts.split_on` and `audio.stt.engine` from `/api/config`; addresses and keys stay on the server
(`backend/open_webui/main.py:2403-2413`, `:2448`).

Saving publishes a `config.updated` event with the two engine names (`backend/open_webui/routers/audio.py:312-322`).

### 7.2 Personal Settings (Settings > Audio)

Labels and descriptions are dotted keys resolved in `src/lib/i18n/locales/en-US/translation.json:2771-2796`; the
component is `src/lib/components/chat/Settings/Audio.svelte`.

| Section | Label | Description (verbatim) | Choices and default | Stored as (`user.settings.ui`) | Source |
|---|---|---|---|---|---|
| STT Settings | **Speech-to-Text Engine** | `Choose the engine used to transcribe voice input.` | `Default` (the server engine) or `Web API`; hidden when the server engine is `Web API` | `audio.stt.engine` | `:190-203` |
| STT Settings | **Language** | `Set a speech recognition language or leave it blank to detect automatically.` | Free text, for example `en`; hidden as above | `audio.stt.language` | `:205-223` |
| STT Settings | **Instant Auto-Send After Voice Transcription** | `Send transcribed voice input immediately after speech recognition finishes.` | Off; saves on change | `speechAutoSend` | `:226-241` |
| TTS Settings | **Text-to-Speech Engine** | `Choose the engine used to read assistant responses aloud.` | `Default` or `Kokoro.js (Browser)` | `audio.tts.engine` (`browser-kokoro`) | `:245-257` |
| TTS Settings | **Kokoro.js Dtype** (Kokoro only) | `Select the local model precision used by Kokoro.js.` | `fp32`, `fp16`, `q8`, `q4` | `audio.tts.engineConfig.dtype` | `:259-276` |
| TTS Settings | **Auto-Playback Response** | `Play assistant responses aloud automatically.` | Off; saves on change | `responseAutoPlayback` | `:278-289` |
| TTS Settings | **Speech Playback Speed** | `Adjust how quickly spoken responses are played.` | Number, `1` (normal) | `audio.tts.playbackRate` | `:291-306` |
| Voice | **Set Voice** (Kokoro) | `Choose the Kokoro.js voice used for speech output.` | Kokoro's voice list | `audio.tts.voice` | `:309-330` |
| Voice | **Set Voice** (browser) | `Choose the browser voice used for speech output.` | `Default` plus the browser's voices | `audio.tts.voice` (the voice's name) | `:349-369` |
| Voice | **Allow non-local voices** (browser) | `Include voices that are not provided by a local speech service.` | Off | `audio.tts.nonLocalVoices` | `:370-375` |
| Voice | **Set Voice** (server engine) | `Choose the configured text-to-speech service voice.` | The server's voice list | `audio.tts.voice` | `:377-397` |

Notes:

- The **Language** tooltip reads `The language of the input audio. Supplying the input language in ISO-639-1 (e.g. en) format will improve accuracy and latency. Leave blank to automatically detect the language.`
  (`src/lib/components/chat/Settings/Audio.svelte:209-213`).
- The browser voice list stores the voice's **name**, while Read Aloud and calls look a browser voice up by its
  **identifier** (`voiceURI`) (`src/lib/components/chat/Settings/Audio.svelte:362-366`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:292`). Where a browser gives the two different values,
  the personal browser voice is not applied (section 14).
- Kokoro is used only when the administrator has chosen a server text-to-speech engine: with `Web API`, Read Aloud
  and calls play the browser voice instead (`src/lib/components/chat/Messages/ResponseMessage.svelte:285`, `:334`;
  `src/lib/components/chat/MessageInput/CallOverlay.svelte:576-593`).
- Defaults for personal settings may also be preset by the administrator's default interface settings, which are
  merged under each user's own choices (`src/lib/components/chat/SettingsModal.svelte:447-449`); whether production
  presets any audio choice is **TO BE CONFIRMED**.

### 7.3 Related Settings Outside the Audio Pages

| Setting | Where | Default | Effect | Source |
|---|---|---|---|---|
| **Voice Mode Prompt** (`task.voice.prompt.enable`, `ENABLE_VOICE_MODE_PROMPT`) | Admin Panel > Settings > Interface; description `Apply voice-specific instructions while voice mode is active.` | on | Adds the voice instructions to call messages | `backend/open_webui/config.py:2385`, `:3153`; `src/lib/components/admin/Settings/Interface.svelte:391-397`; `src/lib/i18n/locales/en-US/translation.json:2536-2537` |
| **Prompt Template** (`task.voice.prompt_template`, `VOICE_MODE_PROMPT_TEMPLATE`) | Same page, shown when the switch is on; description `Defines the behavior used for spoken conversations.` | empty = built-in text beginning "You are a friendly, concise voice assistant." | The instruction text | `backend/open_webui/config.py:2383`, `:2387-2410`, `:3152`; `src/lib/components/admin/Settings/Interface.svelte:399-411`; `src/lib/i18n/locales/en-US/translation.json:2505-2506` |
| **Allow Voice Interruption in Call** | Personal Settings > Interface > Voice; `Let speech interrupt the assistant during a voice call.` | off | Speech cuts the assistant off | `src/lib/components/common/InterfaceSettings.svelte:1855-1874`; `src/lib/i18n/locales/en-US/translation.json:2875-2876` |
| **Display Emoji in Call** | Same; `Show emoji feedback in the call interface.` | off | One extra model request per sentence for an emoji | `src/lib/components/common/InterfaceSettings.svelte:1878-1897`; `src/lib/i18n/locales/en-US/translation.json:2905-2906` |
| `chat.stt`, `chat.tts`, `chat.call` | Admin Panel > Users > Groups | on | Section 3 | `backend/open_webui/config.py:1889-1893` |

### 7.4 A Model's Own Voice

**Workspace > Models**, edit a model, field **TTS Voice** (placeholder `e.g. alloy, echo, shimmer`, suggestions from
the server's voice list). A non-empty value is saved as the model's `tts.voice` and overrides both the user's and
the administrator's voice whenever that model's answers are spoken (`src/lib/components/workspace/Models/ModelEditor.svelte:1276-1287`,
`:414-423`; `src/lib/components/chat/Messages/ResponseMessage.svelte:266-267`).

### 7.5 Environment-Only Settings

Not stored in the database; read at start-up. Live values are **TO BE CONFIRMED**.

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `WHISPER_COMPUTE_TYPE` | `int8` | Precision of local Whisper | `backend/open_webui/config.py:1564` |
| `WHISPER_MODEL_DIR` | `DATA_DIR/cache/whisper/models` (`/app/backend/data/cache/whisper/models` in the image) | Where Whisper models are kept | `backend/open_webui/config.py:1565`; `Dockerfile:98-99` |
| `WHISPER_MODEL_AUTO_UPDATE` | off; always off when `OFFLINE_MODE` is on | When off, the server first tries the model already on disk, and downloads only if that fails | `backend/open_webui/config.py:1566`; `backend/open_webui/routers/audio.py:229-237` |
| `WHISPER_VAD_FILTER` | off | Skip silent stretches in local Whisper | `backend/open_webui/config.py:1568`; `backend/open_webui/routers/audio.py:682` |
| `WHISPER_MULTILINGUAL` | off | Local Whisper multilingual mode | `backend/open_webui/config.py:1570`; `backend/open_webui/routers/audio.py:684` |
| `WHISPER_LANGUAGE` | none | Forces one language for Whisper, OpenAI and Deepgram, overriding every user's language | `backend/open_webui/config.py:1572`; `backend/open_webui/routers/audio.py:969-972` |
| `ELEVENLABS_API_BASE_URL` | `https://api.elevenlabs.io` | ElevenLabs address | `backend/open_webui/config.py:1578` |
| `BYPASS_PYDUB_PREPROCESSING` | off; forced on in the slim image | Skips conversion, compression and splitting before transcription, and conversion of non-MP3 speech | `backend/open_webui/env.py:857`; `backend/open_webui/routers/audio.py:185-189`, `:1138-1140` |
| `USE_SLIM_DOCKER` (build argument `USE_SLIM`) | off | Slim build: no local Whisper, no `Transformers (Local)`, no ffmpeg | `backend/open_webui/env.py:45`; `Dockerfile:140-147` |
| `USE_CUDA_DOCKER` | off | Local Whisper runs on an NVIDIA GPU when CUDA is available, otherwise on the CPU | `backend/open_webui/env.py:47-61`; `backend/open_webui/routers/audio.py:226` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` | off | Adds the user's identity to OpenAI-compatible speech requests | `backend/open_webui/env.py:989` |
| `AIOHTTP_CLIENT_TIMEOUT` | none (no overall limit) | Time limit for speech and transcription requests to outside services | `backend/open_webui/env.py:608-612`; `backend/open_webui/utils/session_pool.py:43` |
| `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` | 10 seconds | Time limit for fetching voice and model lists | `backend/open_webui/env.py:656-663`; `backend/open_webui/routers/audio.py:1348`, `:1422` |
| `OFFLINE_MODE` | off | Turns off Hugging Face downloads and Whisper auto-update | `backend/open_webui/env.py:1201-1204` |

## 8. Cron Jobs and Background Processes

There is **no scheduled job, background loop or Redis listener for audio**. None of the seven loops started at
start-up (inventory, "Background loops") touches speech, and nothing cleans the audio cache (section 6.2).

| What | When it runs | Where | Source |
|---|---|---|---|
| Loading the local Whisper model | On the first transcription after a restart, in each server worker process separately; also during an admin save that selects `Whisper (Local)` | In the request that needs it (in a worker thread) | `backend/open_webui/main.py:776`; `backend/open_webui/routers/audio.py:670-674`, `:305-308` |
| Loading SpeechT5 and the speaker set | On the first `Transformers (Local)` speech request; kept in memory afterwards | In the request | `backend/open_webui/main.py:777-778`; `backend/open_webui/routers/audio.py:326-338`, `:523` |
| Conversion, compression, splitting and local transcription | During the request, in worker threads so other users are not blocked | In the request | `backend/open_webui/routers/audio.py:1142-1169`, `:689` |
| Transcribing an attached recording | After the upload response, as the upload's background processing task | FastAPI background task of `POST /api/v1/files/` | `backend/open_webui/routers/files.py:435-446`, `:152-165` |
| Delivering audio events to webhooks and event functions | Immediately after the speech, transcription or save | In-process tasks | `backend/open_webui/events.py:1062-1071`, `:1159-1171` |

In the browser, the call screen runs its own loops while open: sound detection on every animation frame, and a
player loop that checks for the next sentence every 200 milliseconds
(`src/lib/components/chat/MessageInput/CallOverlay.svelte:317-376`, `:560-610`). Kokoro runs in a web worker
(`src/lib/workers/KokoroWorker.ts:25`). Several screens poll every 100 milliseconds until the browser reports its
voices (`src/lib/components/chat/Messages/ResponseMessage.svelte:287-309`;
`src/lib/components/chat/MessageInput/CallOverlay.svelte:402-423`; `src/lib/components/chat/Settings/Audio.svelte:60-67`).

Settings take effect at save time: the admin save writes the `config` rows and (for Whisper) loads the model at
once (`backend/open_webui/routers/audio.py:298-310`). In a deployment with several workers, the model is loaded in
the worker that handled the save; the others load it on their first transcription.

## 9. Notifications and Emails

- **No email.** The application sends none (ground truth).
- **No in-app or browser notifications** come from this area: the audio events are not among the events that
  create notifications (`backend/open_webui/events.py:669-675`). Users see only pop-ups (section 10).
- **Events.** The audio router publishes three events to the event system, which passes them to administrator
  event webhooks whose filter matches (the default filter `*` matches everything) and to installed Event
  functions (`backend/open_webui/events.py:1046-1059`, `:766-777`, `:1171`):

| Event | When | Data carried (besides the acting user) | Source |
|---|---|---|---|
| `audio.speech_requested` (`Speech requested`) | Every speech request, cached or not | Engine and `cached`; for a new speech also the model and **the first 300 characters of the text being spoken** (`input_preview`) | `backend/open_webui/events.py:642-644`; `backend/open_webui/routers/audio.py:631-637`, `:655-666` |
| `audio.transcription_requested` (`Transcription requested`) | Every successful transcription through the endpoint | The uploaded file name, its type and the language | `backend/open_webui/events.py:645-649`; `backend/open_webui/routers/audio.py:1307-1317` |
| `config.updated` (`Config updated`), subject `audio` | Every admin save of the Audio page | The two engine names | `backend/open_webui/events.py:60-62`; `backend/open_webui/routers/audio.py:312-322` |

  The acting user is described by id, name, email and role (`backend/open_webui/events.py:704`, `:974-985`).
  An event webhook therefore receives personal data and fragments of chat answers; which webhooks production has,
  and where they deliver, is **TO BE CONFIRMED** (see `admin-settings-panels.md` for the event webhook settings).
- **No socket events** are sent by the audio router. Inside the browser, the chat screen tells the call screen
  about each answer with page-internal events named `chat:start`, `chat` and `chat:finish`
  (`src/lib/components/chat/Chat.svelte:3471-3477`, `:1938-1945`, `:2872-2879`).

## 10. Error, Warning and Notice Messages (Verbatim)

Severity: **Error** (red pop-up), **Success** (green pop-up), **Info** (neutral pop-up), **Inline** (text on the
page), **Not shown** (the server answers with the text but no screen displays it), **Log** (server standard
output), **Console** (the browser's developer console, visible only to someone who opens it). Values in `{braces}`
are filled in at run time. Every plain i18n key quoted below displays exactly as written, because the `en-US` file
leaves those keys empty (for example `src/lib/i18n/locales/en-US/translation.json:890`, `:1474`, `:3120`).

**Where server text appears.** The browser shows the server's `detail` text unchanged and untranslated
(`src/lib/apis/audio/index.ts:83-95`, `:120-133`):

| Feature | How a server message is shown | Source |
|---|---|---|
| Dictation (composer, channel, notes, knowledge text window) | Red pop-up; the dictation bar closes and nothing is inserted | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:186-193` |
| Voice call, each turn | Red pop-up; the call keeps listening | `src/lib/components/chat/MessageInput/CallOverlay.svelte:167-174` |
| Attached recording | The file is marked failed and carries the text (display described in `files-uploads-and-storage.md`) | `backend/open_webui/routers/files.py:258-268` |
| Read Aloud | Red pop-up, once per sentence still to be spoken | `src/lib/components/chat/Messages/ResponseMessage.svelte:368-375` |
| Voice call, each spoken sentence | **Not shown** (browser console only) | `src/lib/components/chat/MessageInput/CallOverlay.svelte:534-540` |
| Admin Audio save | **Not shown**: the save has no error handler, so only the missing `Settings saved successfully!` reveals a refusal | `src/lib/components/admin/Settings/Audio.svelte:136-186`, `:240-245` |

A failure that does not come back as a JSON error (server unreachable, a plain-text `Internal Server Error`, or
something in front of the server rejecting the request) produces no message at all on any of these paths
(`src/lib/apis/audio/index.ts:83-97`); section 10.10 lists the other silent failures.

**"Open WebUI" in MedIT GPT errors.** `Open WebUI: Server Connection Error` keeps the upstream name although the
product is branded MedIT GPT: each occurrence is marked as a licence-protected identifier that may not be altered
(`backend/open_webui/routers/audio.py:346-349`, `:768-771`, `:821-824`, `:953-958`, `:1126-1131`). Users seeing
"Open WebUI" in a speech error are seeing expected text, not a different service.

**Control names users may quote.** Tooltips and accessible names, not messages: `Dictate` and `Voice Input` (chat
microphone, `src/lib/components/chat/MessageInput.svelte:2632`, `:2663`), `Record voice` (channel microphone,
`src/lib/components/channel/MessageInput.svelte:1022`), `Confirm recording` (the tick,
`src/lib/components/chat/MessageInput/VoiceRecording.svelte:623`), `Voice mode`
(`src/lib/components/chat/MessageInput.svelte:2674`, `:2728`), `Read Aloud`
(`src/lib/components/chat/Messages/ResponseMessage.svelte:1147-1149`), and in a call `Camera`, `Switch camera`,
`Stop camera`, `Mute`, `Unmute` (tooltips add ` (M)`) and `End call`
(`src/lib/components/chat/MessageInput/CallOverlay.svelte:953`, `:1011`, `:1030-1032`, `:1063-1069`, `:1118`). The
dictation bar's cancel **X** has no accessible name (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:471-487`).

### 10.1 Microphone and Dictation

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Permission denied when accessing microphone: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:2639-2651`; also `src/lib/components/channel/MessageInput.svelte:1029-1043`, `src/lib/components/notes/NoteEditor.svelte:1167`, `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:107` | The browser refused the microphone when **Dictate** (or **Record voice**, **Voice Input**) was clicked. `{error}` is the browser's own error name and text, so its wording differs between browsers | Allow the microphone for the site in the browser's site settings and in the operating system's privacy settings, then click again | Which browser and device; whether another application holds the microphone |
| `Permission denied when accessing microphone` | Error | `src/lib/components/chat/MessageInput.svelte:2659-2661`; also `src/lib/components/channel/MessageInput.svelte:1051`, `src/lib/components/notes/NoteEditor.svelte:1181`, `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:121` | The microphone request could not even be made: the code reaches this branch when calling `navigator.mediaDevices.getUserMedia` throws, for example because the page offers no media-device interface (see section 14 on secure pages) | Use a current browser and the normal secure address of the site | Browser version; whether the address is HTTPS (production address **TO BE CONFIRMED**) |
| `Error accessing media devices.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:233-239` | The dictation bar's own microphone request (with echo cancellation, noise suppression and gain control) failed after the composer's first check had passed; the bar closes | Check the microphone is connected and not in use elsewhere, then retry | Console line `Error accessing media devices.` |
| `Error starting recording.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:290-297` | The browser's recorder refused to start | Retry, or try another browser | Console line `Error starting recording:` |
| `Speech recognition error: {error}` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:354-360` | Browser speech recognition (`Web API`, chosen by the administrator or in the user's own settings) reported an error; `{error}` is the browser's short error code; the bar closes | Retry; if it repeats, set the personal **Speech-to-Text Engine** to `Default` (possible only when the administrator's engine is not `Web API`) | Admin engine and personal engine; browser |

### 10.2 Voice Calls

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Select only one model to call` | Error | `src/lib/components/chat/MessageInput.svelte:2678-2683` | **Voice mode** clicked with more than one model selected | Remove the extra models and click again | None |
| `Call feature is not supported when using Web STT engine` | Error | `src/lib/components/chat/MessageInput.svelte:2685-2691` | The administrator's speech-to-text engine, as this page loaded it, is `Web API` (`audio.stt.engine` = `web`); the user's own engine choice does not matter here | None; calls need a server speech-to-text engine | `audio.stt.engine` (live value **TO BE CONFIRMED**) |
| `Permission denied when accessing media devices` | Error | `src/lib/components/chat/MessageInput.svelte:2693-2727` | Either the microphone test failed, or, when the personal text-to-speech engine is `Kokoro.js (Browser)`, loading Kokoro failed: both happen inside the same `try` (`:2706-2717`), so a Kokoro failure shows this microphone message | Allow the microphone; if it is allowed and the personal engine is Kokoro, reload the page or set the personal **Text-to-Speech Engine** to `Default` | Personal Audio settings (screenshot) |
| `Listening...` | Inline | `src/lib/components/chat/MessageInput/CallOverlay.svelte:985-995` | The call is waiting for the user to speak | Speak | None |
| `Thinking...` | Inline | `src/lib/components/chat/MessageInput/CallOverlay.svelte:986-987`, `:200-219` | A turn is being transcribed and sent | Wait | If it persists, the transcription is slow or failed (section 10.5) |
| `Tap to interrupt` | Inline | `src/lib/components/chat/MessageInput/CallOverlay.svelte:990-991` | The assistant is answering or speaking; tapping the text or the picture stops it (`:976-984`) | Tap to stop the assistant | If it stays with no sound, see section 11.12 |
| `Muted` | Inline | `src/lib/components/chat/MessageInput/CallOverlay.svelte:988-989`, `:666-690` | **Mute** or the **M** key; it switches itself off when the assistant next finishes speaking | Click **Unmute** or press **M** | None |
| `Screen Share` | Inline (menu entry) | `src/lib/components/chat/MessageInput/CallOverlay.svelte:55-63` | Offered in the camera switch menu when the browser can capture the screen | Choose it to share the screen instead of a camera | None |
| `Camera` | Inline (menu entry) | `src/lib/components/chat/MessageInput/CallOverlay/VideoInputMenu.svelte:39` | Name shown for a camera whose label is missing (this fallback is not translated; an empty label shows a blank row) | None | None |

### 10.3 Read Aloud and Kokoro

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No content to speak` | Info | `src/lib/components/chat/Messages/ResponseMessage.svelte:274-277`, `:324-329` | Nothing speakable is left: the answer is empty once reasoning and tool sections are removed, or (server and Kokoro engines) once code blocks, tables, emoji and Markdown symbols are stripped (`src/lib/utils/index.ts:1012-1055`, `:1184-1210`) | None; with a server engine or Kokoro, code and tables are not read out | None |
| `Error: KokoroTTS Worker is not initialized yet.` | Error | `src/lib/workers/KokoroWorker.ts:73-76`; shown by `src/lib/components/chat/Messages/ResponseMessage.svelte:348-355` and `src/lib/components/chat/MessageInput/CallOverlay.svelte:520-529` | Personal engine `Kokoro.js (Browser)` and the in-page Kokoro model is still loading or failed to load. After a failed load the worker is kept and not started again (`src/lib/workers/KokoroWorker.ts:19-23`; `src/lib/components/chat/Messages/ResponseMessage.svelte:335-343`), so the message repeats, once per sentence, until the page is reloaded | Reload the page; if it recurs, set the personal **Text-to-Speech Engine** to `Default` | Browser; whether the Kokoro download is reachable (**TO BE CONFIRMED**, section 14) |
| `TTS model not initialized` | Error | `src/lib/workers/kokoro.worker.ts:33-38`, relayed by `src/lib/workers/KokoroWorker.ts:43-47` | The background Kokoro worker was asked to speak before its model loaded; the page-side check above normally answers first. Like every Kokoro error it is shown after the prefix `Error: `, which the browser adds when it turns the error into text (`src/lib/components/chat/Messages/ResponseMessage.svelte:352`) | As above | As above |
| `Error: {message}` | Error | `src/lib/workers/kokoro.worker.ts:48-50`, relayed by `src/lib/workers/KokoroWorker.ts:43-47` | The Kokoro library failed to generate a sentence; `{message}` is the library's text | Retry; set the personal engine to `Default` | Browser, chosen voice and dtype |

Server speech refusals reached through Read Aloud are in section 10.6.

### 10.4 Settings Pages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:832-838` (personal), `:885-890` (admin); `src/lib/components/admin/Settings/Audio.svelte:182-185` | Personal: **Save** on Settings > Audio (the two auto-saving switches show nothing). Admin: a save, or a change of the text-to-speech engine list, that the server accepted | None | Its absence after an admin save means the server refused it (section 10.7) |
| `Loading Kokoro.js...` | Inline | `src/lib/components/chat/Settings/Audio.svelte:331-342` | Personal engine `Kokoro.js (Browser)`: the model is downloading, with a percentage. It is also shown, without a percentage, while no **Kokoro.js Dtype** has been chosen (nothing is loading then, `:124-131`), and it stays if the download fails, because that failure is not caught (`:135-143`) | Choose a dtype and keep the window open; if it never finishes, choose `Default` | Browser; network access to the model download (**TO BE CONFIRMED**) |
| `Please do not close the settings page while loading the model.` | Inline | `src/lib/components/chat/Settings/Audio.svelte:344-346` | Shown with the line above | Keep the Settings window open | None |
| `Invalid JSON format for Parameters` | Error | `src/lib/components/admin/Settings/Audio.svelte:137-144` | Admin: **Additional Parameters** is not valid JSON. It is checked on every save, including the automatic save when the text-to-speech engine changes, and nothing is saved | Correct the JSON (an empty box is allowed) | None |
| `Slim requires external speech providers. Local speech models and audio conversion are unavailable.` | Inline | `src/lib/components/admin/Settings/Audio.svelte:250-256` | Top of the admin Audio page when the server runs the slim build (`features.slim`, `backend/open_webui/main.py:2328`) | None | Which build production runs (**TO BE CONFIRMED**) |
| `This is a default user permission and will remain enabled.` | Inline | `src/lib/components/admin/Users/Groups/Permissions.svelte:856-862`, `:872-878`, `:888-894` | A group's `Allow Speech to Text`, `Allow Text to Speech` or `Allow Call` switch is off while the default permissions grant it | None; the defaults decide (section 3.1) | Default permissions |
| `{detail}` | Error | `src/lib/components/chat/Settings/Audio.svelte:69-71`; `src/lib/components/admin/Settings/Audio.svelte:92-97`, `:122-124` | Fetching the voice or model list was refused. The `/voices` and `/models` endpoints do not fail on a provider problem (they fall back to a default or empty list, section 10.8), so this appears only when the request itself is refused, for example after the session has ended | Reload and sign in again | None |

### 10.5 Transcription Errors From the Server

Shown in dictation, in calls and on attached recordings as described at the top of section 10. HTTP status in
brackets.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (403) | `backend/open_webui/routers/audio.py:1258-1262` (transcription) and `:612-616` (speech); `backend/open_webui/constants.py:70-72` | A non-administrator without `chat.stt` (transcription) or `chat.tts` (speech) | Ask the administrator about access | The user's groups and the default permissions (section 3) |
| `Oops! It seems like the file format you're trying to upload is not supported. Please upload a file with a supported format and try again.` | Error (400) | `backend/open_webui/routers/audio.py:1264-1270`; `backend/open_webui/constants.py:76` | The recording's declared type does not match **Supported MIME Types** (empty means `audio/*` and `video/webm`). Call turns are always declared `audio/wav` (`src/lib/components/chat/MessageInput/CallOverlay.svelte:215`). Attachments are not refused this way: a non-matching attachment is processed as an ordinary file instead (`backend/open_webui/routers/files.py:151-166`) | None | Admin **Supported MIME Types**; log line `file.content_type: %s` |
| `Invalid audio file extension` | Error (400) | `backend/open_webui/routers/audio.py:1272-1281` | The file name's extension is not in `audio.stt.allowed_extensions` (code default `mp3,wav,m4a,webm,ogg,flac,mp4,mpga,mpeg`; not shown on the admin page). Dictation names the file after the recorded type (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:269-280`) | Try another browser | The stored extension list (live value **TO BE CONFIRMED**) |
| `Audio conversion failed. The audio file may be corrupted or empty.` | Error (400) | `backend/open_webui/routers/audio.py:1142-1148`, `:156-166` | The recording needed converting to MP3 (its codec is not one the server passes through, section 5.9) and the conversion failed, for example for an empty or damaged recording | Record again, speaking for longer | Log line `Error converting audio file: {e}` |
| `[ERROR: Error processing audio file]` | Error (400) | `backend/open_webui/routers/audio.py:1156-1164`, `:1208-1248`; `backend/open_webui/constants.py:16-23` | Cutting a recording that is still over 20 MB after compression into pieces failed, including when a piece cannot be made small enough (`Audio chunk cannot be reduced below max file size.`, logged only, `:1240-1242`) | Use a shorter recording | Server log traceback |
| `[ERROR: The server is out of storage space.]` | Error (400) | `backend/open_webui/constants.py:6-13`, `:16-20`; `backend/open_webui/routers/audio.py:1161-1164` | Same step failed with a storage error; the other variants are `[ERROR: Server storage quota exceeded.]`, `[ERROR: Server storage is not writable.]` and `[ERROR: File name is too long.]` | Try later | Escalate as a storage incident |
| `Error transcribing chunk: {transcribe_exc}` | Error (500) | `backend/open_webui/routers/audio.py:1166-1176` | The engine call failed with an error that was not already an HTTP error. For OpenAI-compatible and Deepgram engines the inner text is `External: {msg}` or `Open WebUI: Server Connection Error` (below). For local Whisper it is the model library's error, for example when the model cannot be loaded or downloaded. For Azure and Mistral it is a network error text | Retry later | Server log; whether the engine is reachable |
| `Transcription failed.` | Error (400) | `backend/open_webui/routers/audio.py:1323-1341` | Any other failure: the recording could not be saved to the server cache (for example a full disk), no server engine ran because the stored engine is `Web API` or unknown (a call opened with `?call=true`, or a page loaded before the administrator switched to `Web API`; `:962-984`, `:1186-1188`), or an unexpected error | Reload the page and retry | Server log traceback after the `transcribe:` line |
| `Configure an external speech-to-text engine. Local Whisper is unavailable in slim.` | Error (503) | `backend/open_webui/routers/audio.py:217-219`, `:670-674` | Slim build with the engine still empty (`Whisper (Local)`), for example a configuration carried over from a full build | None | Admin engine choice |
| `Audio file not found` | Error (400) | `backend/open_webui/routers/audio.py:842-843`, `:989-990` | Azure or Mistral engine: the prepared file was missing when the server came to send it (not expected in normal use) | Retry | Server log |
| `File size ({audio_size}MB) exceeds Azure limit of {AZURE_MAX_FILE_SIZE_MB}MB` | Error (400) | `backend/open_webui/routers/audio.py:845-850`, `:74-75` | Azure engine and a file over 200 MB (`{audio_size}` is whole megabytes). Normally the server has already compressed and cut the file into 20 MB pieces, so this is reached only when that preparation is bypassed (slim build or `BYPASS_PYDUB_PREPROCESSING`) | Use a shorter recording | Build type |
| `Azure API key and region are required for Azure STT` | Error (400) | `backend/open_webui/routers/audio.py:852-853`, `:878-879` | Azure engine with no key stored (the region falls back to `eastus`, so the key is what is missing) | None | Admin (keys are never read by tier 1) |
| `Failed to parse Azure response: {e}` | Error (500) | `backend/open_webui/routers/audio.py:910-929` | Azure answered without text; `{e}` is `No transcription found in response` or `Empty transcript in response`, for example after a silent recording | Speak again, closer to the microphone | None |
| `{message}` | Error (Azure's status) | `backend/open_webui/routers/audio.py:934-945` | Azure's own message, passed through for its codes `EmptyAudioFile`, `AudioLengthLimitExceeded`, `NoLanguageIdentified` and `MultipleLanguagesIdentified` | Follow the message (speak, shorten, or use one language) | Admin **Language Locales** for language codes |
| `An error occurred during transcription.` | Error (Azure's status) | `backend/open_webui/routers/audio.py:946-948` | Azure refused the request with any other code; the code is logged | Retry later | Log line `Azure STT error [{azure_code}]: {message}` |
| `File size exceeds limit of {MAX_FILE_SIZE_MB}MB` | Error (400) | `backend/open_webui/routers/audio.py:992-994`, `:72-73` | Mistral engine and a file over 20 MB; reachable only when preparation is bypassed, as for Azure above | Use a shorter recording | Build type |
| `Mistral API key is required for Mistral STT` | Error (400) | `backend/open_webui/routers/audio.py:1000-1001` | Mistral engine with no key stored | None | Admin |
| `Mistral chat transcription requires MP3 or WAV in slim; local conversion is unavailable.` | Error (400) | `backend/open_webui/routers/audio.py:1013-1018` | Slim build, Mistral with **Use Chat Completions API**, and a file not named `.mp3` or `.wav` (dictation recordings are usually `.webm`; call turns are named `.wav`) | None | Admin Mistral mode |
| `Audio conversion failed. Chat completions API requires mp3 or wav format.` | Error (500) | `backend/open_webui/routers/audio.py:1019-1029` | Mistral chat mode could not convert the file to MP3 | Record again | Log line `Audio conversion failed` |
| `Failed to parse Mistral response: {e}` | Error (500) | `backend/open_webui/routers/audio.py:1066-1069`, `:1100-1102`, `:1111-1113` | Mistral answered without text (`Empty transcript in response`), for example after silence | Speak again | None |
| `External: {msg}` | Error (the service's status, or 500) | Speech: `backend/open_webui/routers/audio.py:341-360`. Transcription: `:758-767` (OpenAI), `:825-836` (Deepgram), `:949-952` (Azure), `:1117-1125` (Mistral) | The outside speech service refused or failed. The text after `External: ` is the service's own error message, or the raw error when its reply could not be read; Mistral may pass its whole reply text (`:1123`). For OpenAI-compatible and Deepgram transcription it arrives inside `Error transcribing chunk: ` | Retry later; if it persists, report the exact text | Service status and the administrator's key and address (tier 1 never reads keys) |
| `Open WebUI: Server Connection Error` | Error (the service's status, or 500) | `backend/open_webui/routers/audio.py:349` (speech), `:771` (OpenAI), `:824`, `:837` (Deepgram), `:958` (Azure), `:1131` (Mistral); `backend/open_webui/constants.py:130` | No usable message: the service could not be reached, answered an error without a message, or sent something the server could not use (for example a Mistral speech reply without audio, logged `No audio_data in Mistral TTS response`, `:580-582`, or a malformed Deepgram reply, logged `Malformed Deepgram response: {exc}`, `:808-812`) | Retry later | Server log and the service's reachability |

### 10.6 Speech Errors From the Server

Shown by Read Aloud (one pop-up per remaining sentence); never shown during a call. The permission refusal and the
`External: {msg}` and `Open WebUI: Server Connection Error` texts are in section 10.5.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` | Error (404) | `backend/open_webui/routers/audio.py:606-610`; `backend/open_webui/constants.py:78` | The server's text-to-speech engine is `Web API` (empty), but this page still believes a server engine is chosen: pages read the engine names only when they load (`src/routes/+layout.svelte:1269`, `:1289`; nothing in `src/` listens for `config.updated`) | Reload the page | Admin text-to-speech engine |
| `Configure an external text-to-speech engine.` | Error (503) | `backend/open_webui/routers/audio.py:603-605` | Slim build with the engine empty or `transformers` and a speech request arrives (a page loaded before a change, or `transformers` stored from the environment) | Reload the page | Build type and engine |
| `Configure an external text-to-speech engine. Local TTS is unavailable in slim.` | Error (503) | `backend/open_webui/routers/audio.py:326-328`, `:516-519` | Defensive check in the local SpeechT5 path; the endpoint's earlier check (`:603-605`) answers first, so it is not expected to appear | None | None |
| `Invalid JSON payload` | Error (400) | `backend/open_webui/routers/audio.py:644-648` | The speech request body was not JSON; MedIT GPT's own pages send JSON (`src/lib/apis/audio/index.ts:108-119`) | None | Whatever program sent the request |
| `Unsupported TTS engine: {engine}` | Error (400) | `backend/open_webui/routers/audio.py:650-652`, `:592-598` | `audio.tts.engine` holds a value with no handler; the admin list offers only valid values, so this points to a value stored from `AUDIO_TTS_ENGINE` or through the API | None | Admin checks the stored engine |
| `Invalid voice id` | Error (400) | `backend/open_webui/routers/audio.py:444-452` | ElevenLabs: no voice chosen, or a voice not in the account's list (checked only when the list could be fetched) | Choose another voice in Settings > Audio | Admin default voice; model voice (section 7.4) |
| `Mistral API key is required for Mistral TTS` | Error (400) | `backend/open_webui/routers/audio.py:552-558` | Mistral speech with no key stored | None | Admin |
| `TTS returned unsupported format {mime_type}. Configure the provider to return MP3, WAV, Ogg, or another browser-playable audio format.` | Error (502) | `backend/open_webui/routers/audio.py:363-388` | Slim build only: the speech service returned audio of a type the slim build cannot pass on, for example raw PCM | None | Admin provider settings |

### 10.7 Admin Save Refusals (Not Shown)

The admin page shows no pop-up for these; the save simply produces no `Settings saved successfully!`
(`src/lib/components/admin/Settings/Audio.svelte:136-186`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Local Whisper is unavailable in slim. Select an external speech-to-text engine.` | Not shown (400) | `backend/open_webui/routers/audio.py:291-295` | Slim build: saving `Whisper (Local)` while another engine is stored (the option is greyed out, `src/lib/components/admin/Settings/Audio.svelte:265-267`) | Choose an external engine | Build type |
| `Local TTS is unavailable in slim. Select an external text-to-speech engine.` | Not shown (400) | `backend/open_webui/routers/audio.py:296-297` | Slim build: saving `Transformers (Local)` while another engine is stored (greyed out, `src/lib/components/admin/Settings/Audio.svelte:512-514`) | Choose an external engine | Build type |

A Whisper model that cannot be loaded during the save (a wrong name, or no download possible) ends the request with
an unhandled server error: nothing is shown, the spinner on the download button stops, and **the new model name is
already stored**, because the settings are written before the model is loaded
(`backend/open_webui/routers/audio.py:298-310`; `src/lib/components/admin/Settings/Audio.svelte:188-192`). The worker
keeps any model it had loaded; other workers, and every worker after a restart, then fail each transcription with
`Error transcribing chunk: {transcribe_exc}`.

### 10.8 Server Log Lines That Explain Symptoms

Log lines, not user messages (rule: support reads them only through whoever holds the logs; log access and
retention are **TO BE CONFIRMED**). The default log level is `INFO` (`backend/open_webui/env.py:113-124`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `transcribe: %s %s` | Log (info) | `backend/open_webui/routers/audio.py:1136` | Every transcription: the cache file path and the language sent | None | Correlate with the user's time |
| `file.content_type: %s` | Log (info) | `backend/open_webui/routers/audio.py:1263` | Every dictation or call turn: the type the browser declared | None | Explains the unsupported-format refusal |
| `Detected language '%s' with probability %f` | Log (info) | `backend/open_webui/routers/audio.py:686` | Local Whisper: the language it heard | None | Evidence for "wrong language" (section 11.4) |
| `Mistral STT - model: %s, method: %s` | Log (info) | `backend/open_webui/routers/audio.py:1006-1010` | Each Mistral transcription | None | Which Mistral mode ran |
| `Bypassing pydub preprocessing (BYPASS_PYDUB_PREPROCESSING=true)` | Log (info) | `backend/open_webui/routers/audio.py:1138-1140` | Conversion, compression and cutting are skipped (always in the slim build) | None | Explains size and format refusals |
| `Error getting audio format: {e}` | Log (error) | `backend/open_webui/routers/audio.py:151-153` | The server could not read the recording's format (for example missing ffmpeg tools); the file is sent on unconverted | None | Server image |
| `Error converting audio file: {e}` | Log (error) | `backend/open_webui/routers/audio.py:164-166` | Conversion to MP3 failed; precedes the `Audio conversion failed.` messages | None | As above |
| `WhisperModel initialization failed, attempting download with local_files_only=False` | Log (warning) | `backend/open_webui/routers/audio.py:232-237` | The local Whisper model was not usable from disk; a download is attempted (slow first transcription, or failure when offline) | None | Network and `WHISPER_MODEL_DIR` |
| `Malformed Deepgram response: {exc}` | Log (error) | `backend/open_webui/routers/audio.py:808-812` | Deepgram's reply had no transcript where expected | None | Deepgram status |
| `Error parsing Azure response` | Log (error, with traceback) | `backend/open_webui/routers/audio.py:927-929` | Precedes `Failed to parse Azure response: {e}` | None | None |
| `Azure STT error [{azure_code}]: {message}` | Log (error) | `backend/open_webui/routers/audio.py:946-948` | Azure refused with a code that is not shown to users | None | The code identifies the cause for the administrator |
| `Error parsing Mistral response` | Log (error, with traceback) | `backend/open_webui/routers/audio.py:1111-1113` | Precedes `Failed to parse Mistral response: {e}` | None | None |
| `TTS returned {mime_type} but BYPASS_PYDUB_PREPROCESSING is set; writing raw audio without transcoding` | Log (warning) | `backend/open_webui/routers/audio.py:185-189` | An OpenAI-compatible speech service returned non-MP3 audio and conversion is bypassed | None | Whether the browser can play that type |
| `Speaker embedding not found for %s, using default index %s` | Log (debug) | `backend/open_webui/routers/audio.py:528-532` | `Transformers (Local)`: the model field is not a known speaker name, so a fixed default speaker is used | None | Explains a voice that ignores the setting |
| `Error fetching voices from custom endpoint: {e}` | Log (error) | `backend/open_webui/routers/audio.py:1437-1439` | A non-OpenAI address did not answer the voice list; the six standard voice names are offered instead (`:1409-1416`) | None | Voice list looks generic |
| `Error fetching models from custom endpoint: {e2}` | Log (error) | `backend/open_webui/routers/audio.py:1374-1376` | Same for the model list; `tts-1` and `tts-1-hd` are offered instead | None | None |
| `Error fetching models: {e}` | Log (error) | `backend/open_webui/routers/audio.py:1395-1396` | ElevenLabs model list failed; the list is empty | None | None |
| `Error fetching ElevenLabs voices: {e}` | Log (warning) | `backend/open_webui/routers/audio.py:1457-1459` | ElevenLabs voice list failed; the list is empty and the voice check is skipped | None | None |
| `Error fetching Azure voices: {e}` | Log (error) | `backend/open_webui/routers/audio.py:1477-1479` | Azure voice list failed; the list is empty | None | None |
| `Error fetching Mistral voices: {e}` | Log (error) | `backend/open_webui/routers/audio.py:1503-1504` | Mistral voice list failed; the list is empty | None | None |
| `Chunk paths: {chunk_paths}` | Log (printed) | `backend/open_webui/routers/audio.py:1158` | Every prepared transcription: the piece file paths (more than one means the recording was cut) | None | None |

At the `DEBUG` level the server also writes **transcripts** to the log (`log.debug(data)`,
`backend/open_webui/routers/audio.py:695`, `:924`, `:1108`); see section 14.

### 10.9 Browser Console Lines

Visible only in the user's browser developer tools; useful when a user or the maintainer reproduces a problem.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Audio blob too small or empty, skipping transcription` | Console | `src/lib/components/chat/MessageInput/CallOverlay.svelte:159-162` | A call turn under 100 bytes was dropped | None | None |
| `Audio for "{content}" not yet available in the cache, re-queued...` | Console | `src/lib/components/chat/MessageInput/CallOverlay.svelte:594-598` | Repeats every 200 ms while a call sentence has no audio; the usual sign of a failed speech request in a call. The line contains the answer text | Tap to interrupt | Section 11.12 |
| `Error synthesizing speech:` | Console | `src/lib/components/chat/MessageInput/CallOverlay.svelte:550-552` | Speech for a call sentence failed | None | None |
| `Error playing audio:` | Console | `src/lib/components/chat/MessageInput/CallOverlay.svelte:584-590` | A call sentence could not be played | None | None |
| `Error accessing webcam: ` | Console | `src/lib/components/chat/MessageInput/CallOverlay.svelte:82-86` | The camera could not be started in a call (no pop-up) | Check camera permission | Section 11.13 |
| `Speech recognition turned off due to inactivity.` | Console | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:333-337` | Browser recognition stopped two seconds after the last words | None | None |
| `Wake Lock request failed:` | Console | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:72-74` | The device refused to keep the screen awake during dictation | None | None |
| `KokoroWorker is already initialized.` | Console | `src/lib/workers/KokoroWorker.ts:19-23` | A second Kokoro start was skipped; after a failed start this is why Kokoro does not recover until the page is reloaded | Reload the page | None |

The call screen also prints each transcript (`src/lib/components/chat/MessageInput/CallOverlay.svelte:177`), each
answer sentence (`:578-586`, `:640`, `:649`) and, with the camera on, the full camera still as a data address (`:143-144`)
to the console; a console screenshot can therefore contain chat content and a picture of the user.

### 10.10 Failures That Show No Message

| What fails | What the user sees | Source |
|---|---|---|
| A transcription or speech request fails without a JSON error (server unreachable, plain-text server error, an upload rejected in front of the server) | Dictation: the bar closes and nothing is inserted. Read Aloud: three dots that ignore clicks. Call: nothing | `src/lib/apis/audio/index.ts:83-97`, `:120-133`; `src/lib/components/chat/Messages/ResponseMessage.svelte:318`, `:1155-1164` |
| Speech for a call sentence fails (server engine) | `Tap to interrupt` with silence; the microphone is ignored unless voice interruption is on | `src/lib/components/chat/MessageInput/CallOverlay.svelte:534-546`, `:594-598`, `:323-340` |
| The first Kokoro load fails when Read Aloud is clicked | Three dots on that answer; later clicks elsewhere give `Error: KokoroTTS Worker is not initialized yet.` | `src/lib/components/chat/Messages/ResponseMessage.svelte:334-343` |
| The camera is refused in a call | Nothing happens on **Camera** | `src/lib/components/chat/MessageInput/CallOverlay.svelte:1030-1038`, `:76-88` |
| The microphone disappears during a call | The call keeps showing `Listening...` | `src/lib/components/chat/MessageInput/CallOverlay.svelte:233-243` (not caught) |
| Browser engine (`Web API`) in a browser without speech recognition | The bar records, the tick closes it, nothing is inserted | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:181-184`, `:300-302` |
| The browser never reports any speech voices (`Web API` speech) | Read Aloud and calls stay silent | `src/lib/components/chat/Messages/ResponseMessage.svelte:285-309`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:398-424` |
| One piece of an answer cannot be played | The rest of that answer is not played: the queue moves on only when a piece ends | `src/lib/utils/audio.ts:19-22`, `:53-63` |
| The transcript is empty | Dictation inserts nothing; a call turn is not sent | `src/lib/components/chat/MessageInput.svelte:1744-1757`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:176-183` |
| An admin save is refused, or the Whisper model cannot be loaded | No success pop-up (section 10.7) | `src/lib/components/admin/Settings/Audio.svelte:136-192` |
| A voice or model list cannot be fetched from the provider | A shorter, generic or empty list (section 10.8) | `backend/open_webui/routers/audio.py:1344-1506` |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes data, settings, roles or access. It may guide users through their **own**
Settings > Audio and Settings > Interface choices. Useful identifiers for any escalation: which feature (dictation,
Read Aloud, voice call, attached recording); the chat id (the part after `/c/` in the address); the approximate
time; the model name shown above the answer; the exact text of any pop-up; the browser, its version and the
device; whether another browser or device behaves the same; and a screenshot of the user's Settings > Audio page,
which shows no keys. **Do not ask users to paste transcripts or answers**: MedIT GPT chats may contain health
information, so ask for a description ("French was typed as English") instead. The support mailbox, queue and
hours are **TO BE CONFIRMED**.

**Reading the administrator's engine from a user's screen.** Users cannot see the admin settings, but their own
Settings > Audio page reveals the engines: the **Speech-to-Text Engine** and **Language** rows are hidden when the
administrator's speech-to-text engine is `Web API` (`src/lib/components/chat/Settings/Audio.svelte:190-224`), and
unless the personal text-to-speech engine is `Kokoro.js (Browser)`, the **Voice** section shows **Allow non-local
voices** when the administrator's text-to-speech engine is `Web API` but a free-text voice box described as the
configured service voice when it is a server engine (`:309-398`).

### 11.1 "There's no microphone, speaker or call button"

**Symptom.** The **Dictate** microphone, the **Read Aloud** speaker or the round **Voice mode** button is missing.

**Likely causes, in order.**
1. An answer is still being written: a **Stop** button replaces the microphone until it finishes
   (`src/lib/components/chat/MessageInput.svelte:2603-2631`).
2. **Voice mode** shows only while the text box is empty and nothing is attached, otherwise **Send message** takes
   its place (`src/lib/components/chat/MessageInput.svelte:2671`, `:2734-2745`).
3. On earlier answers the speaker appears only when the pointer is over the answer; it is always visible on the
   last answer and in high-contrast mode (`src/lib/components/chat/Messages/ResponseMessage.svelte:1151-1153`).
4. The page is read-only, such as a shared chat, which never shows Read Aloud (`:1146`).
5. The permission is not granted: `chat.stt` (microphone), `chat.tts` (speaker) or `chat.call` (call) is off in
   the default permissions and in every group the user belongs to (section 3).

**Diagnostic steps.** Ask which button, whether an answer was being written, whether the text box was empty, and
whether the speaker appears when hovering over the last answer. Compare with a colleague in the same groups.

**Resolution.** Wait for the answer to finish, clear the text box, or hover over the answer. A missing permission
is an access decision for an administrator.

**Escalation.** The user's account (as recorded in the ticket), the missing button, and whether colleagues have it;
the administrator checks the group and default permissions.

### 11.2 "The microphone button does nothing"

**Symptom.** Clicking the microphone shows a red pop-up, or the dictation bar opens and closes with nothing typed.

**Likely causes, in order.**
1. The browser or operating system blocked the microphone: `Permission denied when accessing microphone: {error}`
   (section 10.1).
2. The page cannot use media devices at all: the same text without a detail (section 10.1); an old browser, or a
   page that is not served securely (section 14).
3. The microphone is disconnected or held by another application: `Error accessing media devices.`
4. Browser speech (`Web API`): the browser has no speech recognition, so nothing is typed and no message appears,
   or it reports `Speech recognition error: {error}` (sections 10.1, 10.10).
5. The upload failed without a readable error (network, or something in front of the server rejecting it): the bar
   closes silently (section 10.10).
6. A server refusal after the tick, shown as a red pop-up (section 11.3).
7. Using **Cmd+Shift+L** with keyboard shortcuts turned off (section 2.3).

**Diagnostic steps.** Get the exact pop-up text. Ask the user to open the browser's site settings (usually the
padlock beside the address) and check the microphone permission, and the operating system's microphone privacy
setting. Ask whether their personal **Speech-to-Text Engine** is `Web API`, and whether another browser works.

**Resolution.** Guide the user to allow the microphone and retry; close other applications using it; reload the
page. If their personal engine is `Web API` and the browser lacks recognition, they can choose `Default` (offered
only when the administrator's engine is not `Web API`).

**Escalation.** If several users are affected, or the bar closes silently for everyone: time, browser, and whether
attached recordings also fail. The maintainer checks the server log around the time (`transcribe:` lines, section
10.8) and anything in front of the server (**TO BE CONFIRMED**).

### 11.3 "I get 'Transcription failed.' or an error mentioning 'Open WebUI' or 'External'"

**Symptom.** After dictating, during a call, or on an attached recording, a red pop-up or a failed file shows one of
the server texts in section 10.5.

**Likely causes, in order.**
1. `External: {msg}`: the outside speech service refused the request; the rest of the text is that service's own
   explanation (for example an invalid key or a quota).
2. `Open WebUI: Server Connection Error` (alone or after `Error transcribing chunk: `): the service could not be
   reached or gave no usable answer. "Open WebUI" is the upstream product name kept by licence (section 10).
3. `Error transcribing chunk: {transcribe_exc}` with other text: often the local Whisper model could not be loaded or
   downloaded.
4. `Transcription failed.`: the server could not store the recording (for example a full disk), or no server engine
   is selected (the administrator chose `Web API` after the user's page loaded, or the call was opened with
   `?call=true` while the engine is `Web API`).
5. A permission, type, extension or size refusal (sections 10.5, 11.5).

**Diagnostic steps.** Record the exact text and time. Ask the user to reload the page and try once more (this picks
up any engine change). Ask whether colleagues see the same text.

**Resolution.** Reload and retry; if `External:` or `Open WebUI:` persists, the user cannot fix it.

**Escalation.** The exact text, time and feature. The maintainer checks the speech-to-text engine, the outside
service's status and the server log (section 10.8); keys and addresses are checked by the administrator, never by
tier 1.

### 11.4 "Transcription is wrong or in the wrong language"

**Symptom.** The typed text is in another language, misses words, or is inaccurate.

**Likely causes, in order.**
1. No personal **Language** is set, so the engine guesses the language, which can go wrong on short or mixed
   recordings (tooltip: `src/lib/components/chat/Settings/Audio.svelte:209-213`; local Whisper logs its guess,
   section 10.8).
2. The language was typed in the wrong form. The field expects a two-letter ISO-639-1 code such as `en` or `fr`
   (`:209-219`). OpenAI-compatible and Deepgram engines retry without the language when the first attempt fails, so
   a code the service rejects can quietly become a guess (`backend/open_webui/routers/audio.py:712-750`, `:787-802`); local Whisper
   gets the code as typed with no retry (`:679-685`).
3. A server-wide `WHISPER_LANGUAGE` overrides every user's language for Whisper, OpenAI-compatible and Deepgram
   engines (`backend/open_webui/routers/audio.py:969-972`; live value **TO BE CONFIRMED**).
4. Azure ignores the personal language and listens for the administrator's **Language Locales** (13 common locales
   when empty) (`backend/open_webui/routers/audio.py:854-876`).
5. Browser speech (`Web API`): the code sets no recognition language, so the browser decides
   (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:307-317`).
6. Model and audio quality: local Whisper's code default model is `base` (`backend/open_webui/config.py:1562`;
   production model **TO BE CONFIRMED**); noise and distance from the microphone matter even with noise
   suppression on (`src/lib/components/chat/MessageInput/VoiceRecording.svelte:224-232`).
7. Long recordings are cut into pieces at fixed time points with no overlap, so a word spoken across a cut can be
   lost or split (`backend/open_webui/routers/audio.py:1208-1248`).

**Diagnostic steps.** Ask which feature, which language was spoken, and what the personal **Language** field
contains (if the row is hidden, the browser engine is in use, see the start of this section). Ask whether short,
single-language dictation works.

**Resolution.** Guide the user to type the two-letter code (for example `fr`) in Settings > Audio > **Language**,
click **Save** and retry; to speak close to the microphone in a quiet place; and to dictate in shorter pieces.

**Escalation.** The language expected, the **Language** field value, the feature and time. The maintainer checks
the engine, `WHISPER_LANGUAGE`, the Whisper model and the `Detected language` log line.

### 11.5 "It says the file is too large"

**Symptom.** Attaching or dictating a recording gives a size or format message, or the recording fails.

**Likely causes, in order.**
1. The general upload limit for attachments: `File size should not exceed {maxSize} MB.`
   (`src/lib/components/chat/MessageInput.svelte:1110-1124`; the limit and its live value are in
   `files-uploads-and-storage.md`).
2. An engine limit, reached only when the server's preparation is bypassed (slim build or
   `BYPASS_PYDUB_PREPROCESSING`; otherwise the server compresses and cuts recordings into 20 MB pieces):
   `File size ({audio_size}MB) exceeds Azure limit of {AZURE_MAX_FILE_SIZE_MB}MB` (200 MB) or
   `File size exceeds limit of {MAX_FILE_SIZE_MB}MB` (20 MB, Mistral) (section 10.5).
3. The outside service's own limit, shown as `External: {msg}`, when whole files are passed on unprepared
   (`backend/open_webui/routers/audio.py:1138-1140`; each service's limit is **TO BE CONFIRMED**).
4. A very long recording that cannot be cut: `[ERROR: Error processing audio file]`.
5. Format rather than size: `Oops! It seems like the file format you're trying to upload is not supported. Please upload a file with a supported format and try again.`
   (dictation and calls only, when **Supported MIME Types** excludes the recording), `Invalid audio file extension`,
   or `Audio conversion failed. The audio file may be corrupted or empty.`
6. A size limit in front of the server, which shows no message at all (**TO BE CONFIRMED** for production).

**Diagnostic steps.** Ask for the file's size and type (from the computer's file details), whether it was attached
or dictated, and the exact text.

**Resolution.** Suggest a shorter recording, splitting it into parts, or saving it as MP3 before attaching.

**Escalation.** Text, file size and type, feature, time. The maintainer checks the build type, the engine, **Supported
MIME Types**, `audio.stt.allowed_extensions` and any proxy limit.

### 11.6 "Read aloud is silent"

**Symptom.** Clicking the speaker plays nothing, keeps showing three dots, or shows the crossed speaker in silence.

**Likely causes, in order.**
1. The device, browser tab or system output is muted.
2. Browser speech (`Web API`): the browser has not reported any voices, and nothing is spoken until it does
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:285-309`).
3. A server speech failure: one red pop-up per sentence, such as `External: {msg}` or
   `Open WebUI: Server Connection Error` (section 10.6).
4. The page is older than an engine change by the administrator: `We could not find what you're looking for :/`
   (section 10.6).
5. A failure with no readable error: the three dots stay and ignore clicks (section 10.10).
6. Kokoro did not load (section 11.9).
7. One piece could not be played, which stops the rest of that answer (`src/lib/utils/audio.ts:19-22`, `:53-63`).
8. **Speech Playback Speed** holds an unusual value; the field accepts any number from 0 upward
   (`src/lib/components/chat/Settings/Audio.svelte:291-306`).
9. Moving to another page or chat stops speech (`src/lib/components/chat/Chat.svelte:1577-1584`).

**Diagnostic steps.** Ask what the icon shows, whether a pop-up appeared (exact text), whether a short answer works,
and whether another browser works. Use the start of this section to tell browser speech from a server engine.

**Resolution.** Unmute; reload the page (clears stuck dots and picks up engine changes); set **Speech Playback
Speed** to `1` and click **Save**; if the personal **Text-to-Speech Engine** is `Kokoro.js (Browser)`, try
`Default`.

**Escalation.** Pop-up text, chat id, time, browser. The maintainer checks the text-to-speech engine and the server
log.

### 11.7 "Read aloud says 'No content to speak' or skips code and tables"

**Symptom.** Read Aloud shows `No content to speak`, leaves out parts of the answer, or reads symbols aloud.

**Likely causes, in order.**
1. Reasoning and tool sections are left out (`src/lib/components/chat/Messages/ResponseMessage.svelte:203-204`).
2. With a server engine or Kokoro, code blocks, tables, emoji and Markdown symbols are removed first, and links are
   read as their text (`src/lib/utils/index.ts:1012-1055`); an answer that is only code or a table therefore has
   nothing left (section 10.3).
3. With browser speech (`Web API`) the visible answer is passed whole, without that clean-up, so code and symbols
   can be read out (`src/lib/components/chat/Messages/ResponseMessage.svelte:285-307`).

**Diagnostic steps.** Ask what the answer contains (code, a table) and which engine applies (start of this section).

**Resolution.** Explain the behaviour; there is nothing to fix.

**Escalation.** Not needed.

### 11.8 "The voice sounds different"

**Symptom.** The voice, accent or speed changed, or differs between chats or devices.

**Likely causes, in order.**
1. The administrator changed the default voice: a personal voice stops applying until the user saves Settings >
   Audio again (`src/lib/components/chat/Settings/Audio.svelte:103-107`, `:176`;
   `src/lib/components/chat/Messages/ResponseMessage.svelte:265-270`).
2. The administrator changed the text-to-speech engine, which resets the default voice (section 5.8).
3. The model has its own voice, which wins over everyone's choice (section 7.4); different models can sound
   different.
4. Browser speech: voices come from the device and browser, so another computer sounds different; a personal
   browser voice can also fail to match and fall back to the browser default (section 7.2).
5. Kokoro applies only when the administrator's engine is a server engine; with `Web API` the browser voice is used
   (section 7.2). Lower **Kokoro.js Dtype** precision lowers quality (section 4).
6. **Speech Playback Speed** was changed, or the administrator's **Additional Parameters** change every OpenAI
   speech request (section 7.1).
7. A sentence heard before is replayed from the server's speech cache, which the code does not clear, so it keeps the sound
   it had when first generated (`backend/open_webui/routers/audio.py:618-642`).
8. `Transformers (Local)`: an unknown speaker name falls back to a fixed default speaker (section 10.8); Azure
   voices speak in the language of their own name (`backend/open_webui/routers/audio.py:484-491`).

**Diagnostic steps.** Ask when it changed, which model was used, and for a screenshot of Settings > Audio; ask
whether the same model on another device sounds the same.

**Resolution.** Guide the user to pick their voice again in Settings > Audio and click **Save**, set **Speech
Playback Speed** to `1`, and use the same model and browser as before.

**Escalation.** If it changed for everyone: the date it changed and the model. The administrator checks the
default voice, engine and model voices.

### 11.9 "Kokoro says 'Loading Kokoro.js...' forever"

**Symptom.** With the personal engine `Kokoro.js (Browser)`, the Voice section keeps showing `Loading Kokoro.js...`,
or Read Aloud shows `Error: KokoroTTS Worker is not initialized yet.`

**Likely causes, in order.**
1. No **Kokoro.js Dtype** has been chosen yet; nothing loads until one is (no percentage is shown)
   (`src/lib/components/chat/Settings/Audio.svelte:124-131`, `:331-342`).
2. The first download is slow, or the Settings window was closed during it.
3. The download is blocked or the browser cannot run the model; the failure is not reported
   (`src/lib/components/chat/Settings/Audio.svelte:135-143`; `src/lib/workers/KokoroWorker.ts:31-35`).
4. After one failed load the page does not try again until it is reloaded (`src/lib/workers/KokoroWorker.ts:19-23`).

**Diagnostic steps.** Ask whether a percentage appears, which dtype is selected, whether the device is managed or on
a restricted network, and the browser.

**Resolution.** Choose a dtype, keep the window open until the voice list appears, then reload the page; if it still
fails, set the **Text-to-Speech Engine** back to `Default`.

**Escalation.** Browser and version, network type, whether any percentage appeared. Where the model is downloaded
from is **TO BE CONFIRMED** (section 14).

### 11.10 "I can't start a voice call"

**Symptom.** Clicking **Voice mode** shows a pop-up or nothing opens.

**Likely causes, in order.**
1. The button is missing (section 11.1).
2. `Select only one model to call`: several models are selected.
3. `Call feature is not supported when using Web STT engine`: the administrator's choice (section 10.2).
4. `Permission denied when accessing media devices`: the microphone is blocked, **or** the personal engine is
   Kokoro and it failed to load, which shows the same text (section 10.2).
5. The call opened and closed: the call screen lives in the side panel, and closing that panel ends the call
   (`src/lib/components/chat/Chat.svelte:1586-1592`; `src/lib/components/chat/ChatControls.svelte:196-216`).

**Diagnostic steps.** Get the exact text; ask how many models are selected and whether the personal
**Text-to-Speech Engine** is Kokoro.

**Resolution.** Keep one model; allow the microphone; if Kokoro is selected, reload the page or switch to `Default`.
With `Web API` as the administrator's engine, calls are not available; offer dictation and Read Aloud instead.

**Escalation.** Only for the Web STT message (an administrator decision) or a microphone that works elsewhere.

### 11.11 "Voice call keeps cutting out"

**Symptom.** The call sends half sentences, answers stop midway, speech is not picked up, or the call ends.

**Likely causes, in order.**
1. A pause of two seconds ends the turn and sends what was said so far
   (`src/lib/components/chat/MessageInput/CallOverlay.svelte:359-370`).
2. Background noise counts as speech: turns do not end, or extra turns are made. With **Allow Voice Interruption in
   Call** on, noise also stops the assistant mid-answer (`:323-357`, `:477-483`); with it off, noise picked up
   before an answer starts can still become an extra message, and a new message replaces the answer being spoken
   (`:612-629`).
3. The microphone is muted; it unmutes itself when the assistant finishes speaking (`:666-690`).
4. The call ends when the side panel closes or a new chat starts, which on a phone also closes the panel
   (`src/lib/components/chat/Chat.svelte:1586-1592`, `:2135-2138`).
5. The device would not keep the screen awake, for example in battery-saving mode (failure logged only,
   `src/lib/components/chat/MessageInput/CallOverlay.svelte:707-734`); what a sleeping device does to the call is
   up to the browser (**TO BE CONFIRMED**).
6. Some turns fail to transcribe (red pop-ups, section 10.5), or speech fails (section 11.12).

**Diagnostic steps.** Ask about background noise, speakers versus headphones, the **Allow Voice Interruption in
Call** setting (Settings > Interface > **Voice**), any pop-ups, and whether the side panel was closed or the screen
locked.

**Resolution.** Suggest a quiet place and headphones, avoiding long pauses mid-sentence, turning **Allow Voice
Interruption in Call** off, and keeping the panel open and the screen on.

**Escalation.** Device, browser, chat id, time and any pop-up text, if it happens in a quiet room with headphones.

### 11.12 "The call is stuck on 'Tap to interrupt' or 'Thinking...' and nothing is said"

**Symptom.** The status line stays on `Tap to interrupt` in silence, or on `Thinking...`.

**Likely causes, in order.**
1. Speech for a sentence failed with a server engine; calls show no pop-up and wait on that sentence
   (section 10.10).
2. Kokoro failed (a pop-up appears in this case, section 10.3), or the browser reported no voices (`Web API`).
3. `Thinking...` that lasts: the transcription is slow (for example local Whisper loading its model on the first
   use after a restart, section 8) or failed with a pop-up, or the model is slow to answer.

**Diagnostic steps.** Ask whether a pop-up appeared. Ask the user to end the call and click **Read Aloud** on the
same answer: Read Aloud shows the server's error text that the call hides.

**Resolution.** Tap the status line to stop the assistant and speak again; end the call and use Read Aloud or
reload the page.

**Escalation.** The Read Aloud error text, chat id and time (section 11.6).

### 11.13 "The camera doesn't work in a call"

**Symptom.** **Camera** does nothing, the picture stays dark, or the camera light stays on.

**Likely causes, in order.**
1. The browser refused the camera; no message is shown (section 10.10).
2. The wrong camera is selected; the switch menu lists cameras and, where supported, `Screen Share`, and remembers
   the choice in the browser (`src/lib/components/chat/MessageInput/CallOverlay.svelte:51-74`).
3. The camera check opened at **Camera** is not closed by the code (`:1036`), so the camera can stay in use after
   the camera view is closed; **End call** stops the camera view's own stream (`:1121-1122`).
4. The still sent with each turn helps only if the model accepts images (`:204-213`; see
   `workspace-models-and-model-access.md`).

**Diagnostic steps.** Ask whether the browser asked for the camera, and which camera is selected.

**Resolution.** Allow the camera in the browser's site settings and retry; choose another camera in the switch
menu; reload or close the page if the camera light stays on.

**Escalation.** Not normally needed.

### 11.14 "I saved the Audio settings and nothing happened" (Administrators)

**Symptom.** An administrator clicks **Save** on Admin Panel > Settings > Audio and no `Settings saved successfully!`
appears, or the Whisper download button keeps spinning.

**Likely causes, in order.**
1. A required field is empty: every API key box shown for the chosen engines, and the OpenAI and Mistral address
   boxes, are required by the browser when **Save** is clicked, so the browser shows its own reminder at that field
   (`src/lib/components/common/SensitiveInput.svelte:9`, `:51`; `src/lib/components/admin/Settings/Audio.svelte:296`, `:400`, `:529`, `:582`).
   For an OpenAI-compatible service that needs no key, the browser blocks **Save** while the key box is empty;
   changing the text-to-speech engine list saves without this check (section 5.8).
2. The server refused the save (slim build) or failed loading the Whisper model; no message is shown
   (section 10.7).
3. The Whisper model is still downloading: the save waits for it (section 5.7).
4. `Invalid JSON format for Parameters` (section 10.4).

**Diagnostic steps.** Not tier 1 work beyond collecting the time, the engine chosen and whether a pop-up appeared.

**Resolution.** Escalate to the platform maintainer.

**Escalation.** Time of the save and the engine names (never keys); the maintainer checks the server log. Note that
a failed Whisper load has already stored the new model name (section 10.7).

### 11.15 "Is my voice recorded, and where does it go?"

**Symptom.** A user asks whether recordings are kept, or who hears them.

**What the code shows.** Recordings, converted copies and transcripts, and generated speech with the text it
speaks, are kept in the server cache and the code deletes none of them (section 6.2). Depending on the engines, the
recording or the answer text is sent to an outside service (section 6.4), processed on the MedIT GPT server (local
Whisper, `Transformers (Local)`), or handled in the browser (Kokoro.js; for `Web API` the browser's own speech
service). Event webhooks, if any are set up, receive the first 300 characters of spoken text (section 9).

**Diagnostic steps.** None; do not speculate about which services production uses.

**Resolution.** Explain that the details depend on the institution's configuration, which tier 1 cannot see.
Requests to delete recordings, and any concern that health information reached a service that has not been
approved, go to the platform maintainer and the U of T Privacy Office (privacy.utoronto.ca); tier 1 does not open or
clear the cache.

**Escalation.** The user's account, the approximate dates, and the feature used. Which engines production uses,
retention and approvals are **TO BE CONFIRMED** (section 14).

## 12. Local Customisations

**The audio area matches upstream Open WebUI v0.11.4.** Read-only `git diff main...uoft` shows no change in any file
whose purpose is speech: `backend/open_webui/routers/audio.py`, `src/lib/components/admin/Settings/Audio.svelte`,
`src/lib/components/chat/Settings/Audio.svelte`, `src/lib/components/chat/MessageInput/CallOverlay.svelte`,
`src/lib/components/chat/MessageInput/CallOverlay/VideoInputMenu.svelte`,
`src/lib/components/chat/MessageInput/VoiceRecording.svelte`, `src/lib/workers/KokoroWorker.ts`,
`src/lib/workers/kokoro.worker.ts`, `src/lib/utils/audio.ts`, `src/lib/apis/audio/index.ts`,
`src/lib/components/workspace/Models/TTSVoiceInput.svelte`, `src/lib/components/admin/Users/Groups/Permissions.svelte`,
and the shared files consulted for this area, `backend/open_webui/config.py` (the 30 `audio.*` settings and the
`chat.stt`, `chat.tts`, `chat.call` permissions), `backend/open_webui/routers/files.py`,
`backend/open_webui/utils/misc.py`, `backend/open_webui/events.py` and `backend/open_webui/constants.py`. No
database migration and no setting default differ from upstream (ground truth, "Fork changes").

| Change | Kind | Effect on this area | Source |
|---|---|---|---|
| Hide the task list while **Hide Processing Details** is on | Fork commit `aeed1832c`, one line in the composer | None on the microphone or **Voice mode** buttons, which sit in the same file | `src/lib/components/chat/MessageInput.svelte:1792` |
| **Hide Processing Details** in answers (status history, `Thinking...` indicator, code-execution blocks) | Fork commit `aeed1832c` plus uncommitted working-tree edits | None on Read Aloud: the changed lines are outside `speak()` and the speaker button (`src/lib/components/chat/Messages/ResponseMessage.svelte:272-388`, `:1146-1232`). The `Thinking...` text there is a different message from the call's `Thinking...` (section 10.2) | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:986-987` |
| A resumed answer (after a tool approval) is marked not finished until it ends | Uncommitted working-tree edit | Auto-Playback starts, and the **Dictate** microphone returns, only when such an answer has really finished | `src/lib/components/chat/Chat.svelte:2847-2850`, `:2855-2867`; `src/lib/components/chat/MessageInput.svelte:2629` |
| `en-US` added as a further translation fallback when a default interface language is configured | Uncommitted working-tree edit | Keys that are empty in the user's language, such as the dotted Audio settings labels whose English text exists only in `en-US`, fall back to English | `src/lib/i18n/index.ts:88-118` |
| Product name MedIT GPT | Fork commits | Does not reach speech errors: `Open WebUI: Server Connection Error` is licence-protected and unchanged (section 10) | `backend/open_webui/env.py:951`; `backend/open_webui/routers/audio.py:346-349` |

The only `en-US` text the fork and the working tree change is the **Hide Processing Details** description; no
audio label or message differs from upstream (`git diff main...uoft` and `git diff` on
`src/lib/i18n/locales/en-US/translation.json`).

## 13. Source File Index

Every file this document cites, with what it holds for the audio area. Paths are repository-relative; line numbers
are those of the working tree on 2026-10-10.

### 13.1 Backend

| File | What it holds for this area |
|---|---|
| `backend/open_webui/routers/audio.py` | The whole server side: the six endpoints, engine handlers for speech and transcription, conversion, compression and cutting, the speech cache, voice and model lists, and every server message in sections 10.5 to 10.8 |
| `backend/open_webui/routers/files.py` | Transcription of attached recordings during upload processing, and the failed-file record |
| `backend/open_webui/config.py` | The 30 `audio.*` settings and their environment variables, Whisper variables, the `chat.stt`, `chat.tts`, `chat.call` permission defaults, and the Voice Mode Prompt |
| `backend/open_webui/env.py` | Slim build, `BYPASS_PYDUB_PREPROCESSING`, device type, forwarded user headers, client time limits, offline mode, log level, product name |
| `backend/open_webui/constants.py` | Shared message texts: permission refusal, unsupported format, not found, storage errors, the connection-error identifier |
| `backend/open_webui/events.py` | The `audio.speech_requested`, `audio.transcription_requested` and `config.updated` events and their delivery |
| `backend/open_webui/main.py` | Router mount, start-up state for the Whisper and SpeechT5 models, the audio and slim values sent to browsers |
| `backend/open_webui/utils/misc.py` | `strict_match_mime_type`, the Supported MIME Types check |
| `backend/open_webui/utils/middleware.py` | Adds the Voice Mode Prompt to call messages |
| `backend/open_webui/utils/session_pool.py` | The shared HTTP client used for outside speech services |
| `backend/open_webui/utils/headers.py` | `include_user_info_headers`, used when user details are forwarded to OpenAI-compatible services |
| `backend/open_webui/utils/auth.py` | `get_verified_user` and `get_admin_user` on the audio endpoints |
| `backend/open_webui/models/config.py` | The `config` table holding the `audio.*` rows |
| `backend/open_webui/models/users.py` | `user.settings`, where personal audio choices are stored |
| `backend/open_webui/models/groups.py` | Group permissions JSON |
| `backend/open_webui/models/models.py` | Model `meta`, holding a model's own voice |
| `backend/open_webui/storage/provider.py` | File deletion, which leaves converted copies and transcripts behind |
| `Dockerfile` | ffmpeg and model folders in the image, the slim build argument |

### 13.2 Front End: Speech Components

| File | What it holds for this area |
|---|---|
| `src/lib/components/chat/MessageInput/VoiceRecording.svelte` | The dictation bar: microphone, recorder, browser recognition, upload for transcription |
| `src/lib/components/chat/MessageInput/CallOverlay.svelte` | The voice call screen: sound detection, turns, playback, camera, mute, status texts |
| `src/lib/components/chat/MessageInput/CallOverlay/VideoInputMenu.svelte` | The camera switch menu in a call |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | The Read Aloud button, `speak()`, voice choice, Kokoro and server paths |
| `src/lib/components/chat/MessageInput.svelte` | The **Dictate** and **Voice mode** buttons, their checks and messages, attachment size check |
| `src/lib/components/chat/Chat.svelte` | Hidden audio player, Auto-Playback, call events, the voice flag on call messages, call closing |
| `src/lib/components/chat/ChatControls.svelte` | Places the call screen in the side panel or a drawer |
| `src/lib/workers/KokoroWorker.ts` | Page-side controller for the Kokoro background worker |
| `src/lib/workers/kokoro.worker.ts` | The Kokoro background worker: model load and speech generation |
| `src/lib/utils/audio.ts` | `AudioQueue`, which plays Read Aloud pieces in order |
| `src/lib/utils/index.ts` | Text clean-up and splitting before speech |
| `src/lib/apis/audio/index.ts` | Browser calls to the six audio endpoints and how their errors are passed on |
| `src/lib/constants.ts` | The audio API base address |
| `src/lib/types/index.ts` | The three Response Splitting values |
| `src/lib/stores/index.ts` | Settings type fields for audio and the shared audio stores |
| `src/lib/shortcuts.ts` | The dictation keyboard shortcut |

### 13.3 Front End: Settings, Permissions and Other Screens

| File | What it holds for this area |
|---|---|
| `src/lib/components/admin/Settings/Audio.svelte` | Admin Panel > Settings > Audio: engines, keys, voices, models, splitting, slim notice, save |
| `src/lib/components/chat/Settings/Audio.svelte` | Personal Settings > Audio: engines, language, Kokoro, speed, voice |
| `src/lib/components/chat/SettingsModal.svelte` | The Settings window tabs and the `Settings saved successfully!` pop-ups |
| `src/lib/components/common/InterfaceSettings.svelte` | The personal call options **Allow Voice Interruption in Call** and **Display Emoji in Call** |
| `src/lib/components/admin/Settings/Interface.svelte` | The Voice Mode Prompt switch and template |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | The three speech permission switches and the default-permission notice |
| `src/lib/constants/permissions.ts` | Front-end permission defaults |
| `src/lib/components/common/SensitiveInput.svelte` | Key boxes on the admin page, required by default |
| `src/lib/components/workspace/Models/TTSVoiceInput.svelte` | Voice suggestion box used by the admin page and the model editor |
| `src/lib/components/workspace/Models/ModelEditor.svelte` | A model's own **TTS Voice** |
| `src/lib/components/channel/MessageInput.svelte` | Dictation in channels (**Record voice**) |
| `src/lib/components/notes/NoteEditor.svelte` | Dictation in notes |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte` | Dictation in the knowledge-base text window |
| `src/routes/(app)/+layout.svelte` | `?settings=audio` deep links |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | `/admin/settings/audio` redirect |
| `src/routes/+layout.svelte` | Loads the configuration, including engine names, when the app opens |
| `src/lib/i18n/index.ts` | Translation fallback rules (working-tree change, section 12) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted Audio settings keys; empty plain keys |

## 14. Open Questions

Everything below could not be established from the repository. Items marked **TO BE CONFIRMED** need an answer
from the platform maintainer or the U of T owner named; none of them may be guessed in a guide.

### 14.1 Deployment and Configuration (TO BE CONFIRMED)

1. **Production host name and address**, and whether it is served over HTTPS. Browsers generally offer microphone
   and camera access only to secure pages; that is web-platform behaviour, not something the repository can show,
   and it decides whether `Permission denied when accessing microphone` (section 10.1) can appear for everyone.
2. **Which build production runs** (full or slim, `USE_SLIM_DOCKER`), and whether `BYPASS_PYDUB_PREPROCESSING` is
   set. This decides which size and format messages can appear (sections 10.5, 10.7, 11.5).
3. **The live engines and their settings**: `audio.stt.engine`, `audio.tts.engine`, models, voices, Response
   Splitting, Supported MIME Types and `audio.stt.allowed_extensions` are data in the `config` table (section 7.1);
   the environment-only variables (`WHISPER_MODEL`, `WHISPER_LANGUAGE`, `WHISPER_MODEL_DIR`, `OFFLINE_MODE`,
   `ENABLE_FORWARD_USER_INFO_HEADERS`, time limits) are set in the environment (section 7.5).
4. **Speech permissions in production**: whether `chat.stt`, `chat.tts` and `chat.call` are granted by default or
   only to some groups (section 3).
5. **Administrator default interface presets** for audio choices (section 7.2).
6. **Anything in front of the server** (reverse proxy, gateway) and its upload size limit and time-outs; a refusal
   there shows no message (sections 10.10, 11.5).
7. **Log access and retention** for the audio log lines (section 10.8), and whether production ever runs at the
   `DEBUG` level, which writes transcripts to the log.
8. **Event webhooks and Event functions** in production, and where they deliver (section 9).
9. **Support contacts**: mailbox, queue and hours for escalations (section 11).

### 14.2 Privacy

MedIT GPT chats may contain health information, so every item below is personal data, and possibly personal health
information, until the U of T Privacy Office (privacy.utoronto.ca) says otherwise.

1. **Cached audio holds chat content.** `DATA_DIR/cache/audio/speech/` keeps every generated sentence as audio plus a
   `.json` file containing the spoken text; `DATA_DIR/cache/audio/transcriptions/` keeps every dictated recording, call
   turn, converted copy and transcript; attached recordings leave a converted copy and transcript beside the upload
   (section 6.2). The code deletes none of these, and deleting a chat, a file or a user leaves them in place.
   **Retention, backup, who may clear them and how a deletion request is honoured are TO BE CONFIRMED.**
2. **Which outside services receive audio or text** depends on the engines (section 6.4): the OpenAI-compatible
   address configured for speech-to-text and for text-to-speech (code default `https://api.openai.com/v1`),
   Deepgram (`https://api.deepgram.com/v1/listen`), Microsoft Azure Speech (a regional Microsoft address unless an
   endpoint is set), ElevenLabs (`ELEVENLABS_API_BASE_URL`, default `https://api.elevenlabs.io`) and Mistral (default
   `https://api.mistral.ai/v1`). Recordings go to the speech-to-text service; answer text goes to the
   text-to-speech service. **Which of these production uses, and whether each has been approved for this data
   (for example through a U of T information risk assessment), is TO BE CONFIRMED.**
3. **Attached recordings bypass `chat.stt`.** Turning speech-to-text off for users does not stop attached audio
   files being sent to the speech-to-text engine (section 3.4). Whether that is intended is **TO BE CONFIRMED**.
4. **Browser speech (`Web API`).** What the browser vendor's own speech service does with audio or text, and whether
   it leaves the device, depends on the browser; **TO BE CONFIRMED** per supported browser (section 6.4).
5. **Kokoro.js** keeps text in the browser, but the model download location is the library's default, not set in
   the repository (`src/lib/workers/kokoro.worker.ts:9`, `:21-24`); the download host, whether U of T networks allow
   it, and whether the browser caches the files are **TO BE CONFIRMED**.
6. **Forwarded identity.** With `ENABLE_FORWARD_USER_INFO_HEADERS` on, OpenAI-compatible speech requests carry the
   user's details (section 6.4); the production value is **TO BE CONFIRMED**.
7. **Events** carry the acting user's id, name, email and role and, for speech, the first 300 characters of the
   spoken text (section 9).
8. **Logs.** At the default `INFO` level the log records cache paths, declared file types, languages and errors
   (section 10.8); at `DEBUG` it records transcripts (`backend/open_webui/routers/audio.py:695`, `:924`, `:1108`).
9. **The browser console** records transcripts, answer sentences and, with the camera on, camera stills (section
   10.9). Users should not send console screenshots through ordinary channels.

### 14.3 Security-Sensitive Questions (Referred)

Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

1. Who can retrieve files from the server's audio cache, and how the speech cache is shared between users
   (section 6.2).
2. How the speech-service keys entered on the admin page are protected (their location only is given in section 7).

### 14.4 Behaviour That Depends on Something Outside the Repository

1. The meaning of the browser's codes in `Speech recognition error: {error}` and of the `{error}` text in
   `Permission denied when accessing microphone: {error}` is defined by each browser.
2. What local Whisper (the faster-whisper library) does with a language code it does not recognise; the code passes
   the user's text unchanged and does not retry (section 11.4).
3. Each outside service's own file-size and format limits, which appear as `External: {msg}` (section 11.5).
4. Whether an OpenAI-compatible service accepts a call turn that is named `.wav` but recorded in the browser's own
   format, when the server does not convert it (slim build or bypass; section 5.3).
5. `Transformers (Local)` writes the SpeechT5 audio with the `soundfile` library to a file named `.mp3`
   (`backend/open_webui/routers/audio.py:542`, `:626`); whether that works depends on the library version installed.
6. What a phone or computer does to a running call when its screen sleeps (section 11.11), and whether browsers
   block Auto-Playback before the user has interacted with the page.
7. The browser voice list stores a voice's name while playback matches its identifier (section 7.2); which
   browsers give different values, and so ignore the personal browser voice, needs testing.

### 14.5 Possible Defects Noted for the Maintainer

Observations from reading the code; tier 1 cannot act on them.

1. The admin Audio save has no error handler, so server refusals and failed Whisper loads show nothing
   (section 10.7).
2. The Whisper model name is stored before the model is loaded, so a failed load leaves a setting that breaks
   transcription in other workers and after a restart (section 10.7).
3. A Kokoro load failure on the **Voice mode** button is reported as `Permission denied when accessing media devices`
   (section 10.2); a failed Kokoro load is not retried until the page is reloaded, and the personal settings
   spinner stays when the download fails (sections 10.3, 10.4).
4. Speech failures in a call are silent and leave the call waiting (section 10.10).
5. The Read Aloud queue has no error handler, so one unplayable piece stops the rest of the answer (section 10.10).
6. The call's **Camera** button opens a test camera stream that the code does not close, and the call's own
   microphone request is not guarded (sections 10.10, 11.13).
7. A call opened with `?call=true` skips the Web STT check, so every turn ends with `Transcription failed.` when the
   engine is `Web API` (section 10.5).
8. When no language is set, a failing OpenAI-compatible or Deepgram request is sent twice with the same content,
   because the language list is then two empty entries (`backend/open_webui/routers/audio.py:969-972`, `:712-750`).
9. `Chunk paths: {chunk_paths}` is written with `print`, outside the logger, so it appears whatever the log level
   (`backend/open_webui/routers/audio.py:1158`).
10. The admin key boxes are required by default, so an OpenAI-compatible service without a key cannot be saved with
    **Save** (section 11.14).

### 14.6 Corrections Made to Earlier Sections (2026-10-10)

1. Section 4, **Slim image**: browser speech and Kokoro also work in the slim build; only the two local server
   engines are unavailable.
2. Section 5.3, step 2: the call button refuses more than one model; it does not require exactly one.
3. Section 5.3, points for support: noise stops an answer mid-way only when **Allow Voice Interruption in Call** is
   on; otherwise the effect is an extra turn.

### 14.7 Consistency With the Ground Truth

No contradiction was found. One refinement for `tools/ground-truth.md`, which says the cache folder is "not
configurable separately": that holds for the audio speech and transcription caches (`backend/open_webui/config.py:182`;
`backend/open_webui/routers/audio.py:77`, `:1288`), but the local Whisper models can be moved with
`WHISPER_MODEL_DIR` (`backend/open_webui/config.py:1565`). The full Docker image also downloads the `WHISPER_MODEL`
model into that folder at build time (`Dockerfile:169`, `:177`), so a full-image deployment normally has it on disk
before the first transcription.
