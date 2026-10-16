# Image Generation and Editing

## At a Glance

- **What it is.** MedIT GPT makes and edits pictures by sending the request to an outside
  **engine** chosen on Admin Settings › **Images**: `Default (Open AI)` (any OpenAI-style images
  service, for example DALL·E or GPT-Image), `Gemini`, a self-hosted `ComfyUI` with an uploaded
  workflow, or `Automatic1111` (create only). Creation and editing have separate switches, engines
  and connections; **both switches are off in the code defaults** (sections 1, 4.2, 7.1).
- **How users trigger it.** In a chat: **Integrations** › **Image** (tooltip `Generate an image`),
  then describe the picture. In the default native mode the model calls `generate_image` or
  `edit_image` (`builtin-native-tools.md`); in legacy mode MedIT GPT makes or edits the picture
  before the model answers, optionally after a task model rewrites the prompt. Admins also have
  **Playground › Images** (`/playground/images`) (sections 5.4 to 5.8).
- **Who can.** Gates in order: the admin switch, the `features.image_generation` permission
  (default on), the model's **Image Generation** capability and tool group, and the toggle itself.
  There is no separate edit permission. Admins skip the permission but not the switches (3.2).
- **What users cannot choose.** Size, steps, model and count are site-wide admin settings; Gemini
  receives no size at all; every MedIT GPT path asks for one picture (4.2, 5.11).
- **Where pictures go.** Each picture becomes an ordinary file `generated-image.<ext>` owned by
  the requester, in the normal upload storage (not `cache/image/generations`, which is unused),
  with the prompt copied into the file record; nothing deletes it automatically (section 6).
- **Failures.** Mostly `Something went wrong :/` or `[ERROR: {error}]` (the engine's HTTP status
  phrase only); in chat the model is told the error and usually explains it. There is no image-specific
  time limit, so a busy engine can keep `Creating image` or `Running...` on screen (5.12, 10, 11).
- **Privacy.** Prompts and source pictures leave MedIT GPT for the engine; approval of the services
  for MedIT GPT content is TO BE CONFIRMED (14.5). The area's code matches upstream v0.11.4; the
  fork's **Hide Processing Details** hides the progress lines (section 12).

## 1. Purpose and Who Uses It

MedIT GPT can make a new picture from a written description ("image generation") and change an
existing picture according to an instruction ("image editing"). MedIT GPT does not draw the
pictures itself: it sends the description, and for edits the source pictures, to an outside
**image engine** that an administrator chooses and connects. The finished picture comes back,
is saved as a file in MedIT GPT and is shown in the chat reply or on the image playground page.

| Engine (setting value) | What it is | Create | Edit | Source |
|---|---|---|---|---|
| **Default (Open AI)** (`openai`) | Any service that offers the OpenAI images interface (`/images/generations`, `/images/edits`), for example OpenAI's DALL·E and GPT-Image models | Yes | Yes | `backend/open_webui/routers/images.py:621-679`, `:978-1057`; `src/lib/components/admin/Settings/Images.svelte:328`, `:748` |
| **Gemini** (`gemini`) | Google's Gemini interface, with the `predict` (Imagen) or `generateContent` method | Yes | Yes (`generateContent` only) | `backend/open_webui/routers/images.py:681-737`, `:1059-1114`; `src/lib/components/admin/Settings/Images.svelte:331`, `:750` |
| **ComfyUI** (`comfyui`) | A self-hosted ComfyUI server that runs an admin-supplied workflow | Yes | Yes (separate edit workflow) | `backend/open_webui/routers/images.py:739-793`, `:1116-1198`; `backend/open_webui/utils/images/comfyui.py:189-255` |
| **Automatic1111** (`automatic1111`) | A self-hosted stable-diffusion-webui server started with its API turned on | Yes | **No** (not offered as an edit engine) | `backend/open_webui/routers/images.py:794-840`; `src/lib/components/admin/Settings/Images.svelte:330`, `:744-751` |

Who uses it:

| Who | What they do | Where | Source |
|---|---|---|---|
| **Administrators** | Switch image generation and image editing on or off, choose the engines, enter the engine addresses, keys, model, size and steps, upload ComfyUI workflows, and decide whether a task model first rewrites the user's request into an image prompt | Admin Settings › **Images** | `src/lib/components/admin/Settings/Images.svelte:296-1041`; `backend/open_webui/routers/images.py:271-319` |
| **Signed-in users** with the **Image Generation** feature permission | Ask for a picture in a chat by turning on the composer's image toggle (labelled with the tooltip `Generate an image`), then describing it; the model either calls the `generate_image` or `edit_image` tool (normal "native" mode) or MedIT GPT generates the picture before the model answers ("legacy" mode) | Any chat | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:472-491`; `backend/open_webui/utils/tools.py:687-704`; `backend/open_webui/utils/middleware.py:2711-2720` |
| **Administrators** (playground) | Type a prompt and get a picture directly, or attach pictures and edit them, without a chat model | `/playground/images` | `src/lib/components/playground/Images.svelte` (section 5.8) |
| **Workspace model editors** | Turn a model's **Image Generation** capability, built-in tool group or default feature on or off | Workspace › Models | `src/lib/components/workspace/Models/Capabilities.svelte:29`; `src/lib/components/workspace/Models/BuiltinTools.svelte:53`; `src/lib/components/workspace/Models/DefaultFeatures.svelte:17` |
| **Tier 1 support** | Answer "where is the image button", "why did it fail", "why is it the wrong size"; check the admin page read-only and escalate | Section 11 | — |

The two built-in tools, `generate_image` and `edit_image`, are documented in depth in
`builtin-native-tools.md` (sections 3.2 and 4.3 there); this document covers the engines, the
settings, the endpoints they call, the legacy path, the playground, storage and failures.
Neighbouring documents: `chat-completion-pipeline-and-generation-tasks.md` (where the legacy step
and the image prompt task sit in a chat turn), `files-uploads-and-storage.md` (the file records
pictures become), `admin-settings-panels.md` (the Images tab among the other admin tabs),
`model-connections-openai-ollama-and-direct.md` (the other playground tabs) and
`configuration-persistent-settings-a-to-o.md` (the `image_generation.*` and `images.*` keys in
the full settings catalogue).

Both image switches are **off** in the code defaults (`ENABLE_IMAGE_GENERATION` and
`ENABLE_IMAGE_EDIT` read as true only when set to `true`, `backend/open_webui/config.py:1351`,
`:1525`), so on a fresh installation users see no image toggle until an administrator turns
image generation on. Whether MedIT GPT production has either switch on, and which engine it uses,
is data in the `config` table: **TO BE CONFIRMED** (section 14).

## 2. Navigation and URLs

### 2.1 Screens and Controls

| Where | How to get there | What is there | Source |
|---|---|---|---|
| **Integrations** menu in the message composer | The round button with the tooltip and accessible name `Integrations` to the left of the message box, on `/` (new chat) or `/c/{id}` | A row **Image** with the tooltip `Generate an image` and an on/off switch. The menu button itself appears only when at least one of web search, image, code interpreter, tools, skills or toggle filters is available | `src/lib/components/chat/MessageInput.svelte:2295-2344`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:304-306`, `:471-494` |
| Image chip in the composer | Appears next to the Integrations button while the image switch is on | A blue picture icon with the tooltip `Image`; hovering shows a cross, clicking turns the switch off. **Escape** in the message box also turns it off (with web search and code interpreter) | `src/lib/components/chat/MessageInput.svelte:2502-2519`, `:2169-2177` |
| Generated picture in the reply | Above the reply text in the assistant's message | The picture (accessible text: the file name, or `Generated Image`); progress lines such as `Creating image` appear in the status list at the top of the reply (legacy mode) or as a tool entry (native mode) | `src/lib/components/chat/Messages/ResponseMessage.svelte:720-746`; `backend/open_webui/utils/middleware.py:1871-1876` |
| **Playground › Images** (admins) | Profile menu › **Playground** (shown to admins only), then the **Images** tab; or `/playground/images` | Prompt box, **Add Image**, **Run**, and a grid of results (section 5.8) | `src/lib/components/layout/Sidebar/UserMenu.svelte:425-447`; `src/routes/(app)/playground/+layout.svelte:78-84`; `src/lib/components/playground/Images.svelte:124-281` |
| **Admin Settings › Images** | Settings window, **Images** in the admin **Experience** group (administrators only) | Switches, engines, addresses, keys, model, size, steps, ComfyUI workflows (section 7.1) | `src/lib/components/chat/SettingsModal.svelte:172`, `:310-315`, `:891-896`; `src/lib/components/admin/Settings/Images.svelte:302-304` |
| **Admin Settings › Interface** | Same Settings window, **Interface** | `Image Prompt Generation Prompt`, the template the task model uses to write the image prompt (section 7.3) | `src/lib/i18n/locales/en-US/translation.json:2502-2503`; `chat-completion-pipeline-and-generation-tasks.md` |
| Group or default permissions | Admin Panel › Users › Groups, a group (or the default permissions), **Features Permissions** | Switch `Image Generation` (`features.image_generation`) | `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1061-1078` |
| Model editor | Workspace › Models, edit a model | **Capabilities › Image Generation**, **Builtin Tools › Image Generation** and **Default Features › Image Generation** (section 3.2) | `src/lib/components/workspace/Models/Capabilities.svelte:29-32`; `src/lib/components/workspace/Models/BuiltinTools.svelte:53-56`; `src/lib/components/workspace/Models/DefaultFeatures.svelte:17-20` |

The admin tab title is the dotted key `settings.admin.images.title`, which reads `Images`
(`src/lib/components/admin/Settings/Images.svelte:303`; `src/lib/i18n/locales/en-US/translation.json:2471`).
Its two sections are `Create Image` and `Edit Image`
(`settings.admin.images.sections.createImage.title` and `.editImage.title`,
`src/lib/components/admin/Settings/Images.svelte:319`, `:731`; `translation.json:2467-2468`). The
playground's browser tab reads `Playground / {WEBUI_NAME}`, so "Playground / MedIT GPT" with the
fork's default name (`src/routes/(app)/playground/+layout.svelte:15-17`).

### 2.2 Deep Links

| Link | Effect | Source |
|---|---|---|
| `/?image-generation=true` | A new chat opens with the image switch already on | `src/lib/components/chat/Chat.svelte:2176-2178` (inside `initNewChat`, `:2015`) |
| `/admin/settings/images` | Redirects to `/?settings=admin:images`, which opens the admin Images tab; a non-administrator gets the personal **General** tab instead | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/routes/(app)/+layout.svelte:181-185` |
| `/playground/images` | The images playground; anyone who is not an admin is sent to `/` | `src/lib/components/playground/Images.svelte:115-121` |

### 2.3 Server Endpoints

The images router is mounted at `/api/v1/images` (`backend/open_webui/main.py:849`); the browser
calls it through `src/lib/apis/images/index.ts` (base URL `IMAGES_API_BASE_URL`,
`src/lib/constants.ts:16`).

| Method and path | Who may call it | What it does | Source |
|---|---|---|---|
| `GET /api/v1/images/config` | Admins | Returns the 33 image settings of section 7.1 | `backend/open_webui/routers/images.py:228-273` |
| `POST /api/v1/images/config/update` | Admins | Checks the size and steps (section 7.2), saves every image setting, trims slashes from both ends of the two ComfyUI addresses, then applies the model (for Automatic1111 it also switches the server's loaded checkpoint) | `backend/open_webui/routers/images.py:276-319`, `:172-199` |
| `POST /api/v1/images/verify` | Admins | Tests an Automatic1111 (`/sdapi/v1/options`) or ComfyUI (`/object_info`) address; any other engine is refused | `backend/open_webui/routers/images.py:338-359` |
| `GET /api/v1/images/models` | Any signed-in user (role `user` or `admin`) | Lists the models for the current **generation** engine (section 4.3) | `backend/open_webui/routers/images.py:362-442` |
| `POST /api/v1/images/generations` | Signed-in users, only when **Image Generation** is on and the user is an admin or has `features.image_generation` | Creates pictures from a prompt; used by the playground | `backend/open_webui/routers/images.py:562-593` |
| `POST /api/v1/images/edit` | Signed-in users, only when **Image Edit** is on and the user is an admin or has `features.image_generation` | Edits one or more pictures; used by the playground | `backend/open_webui/routers/images.py:858-893` |
| `POST /api/v1/tasks/image_prompt/completions` | Any signed-in user | Asks the task model to turn the conversation into an image prompt (legacy path, section 5.7). The legacy step calls the same function directly; no screen calls this route | `backend/open_webui/routers/tasks.py:344-400`; `backend/open_webui/utils/middleware.py:1950-1960` |
| `GET /api/v1/files/{id}/content` | The owner, admins, and people with read access (section 3.4) | Serves a stored generated picture | `backend/open_webui/routers/files.py:795-855` |

The chat paths (native tools and the legacy step) do not call these routes over the network; they
call the same functions (`image_generations`, `image_edits`) directly inside the server
(`backend/open_webui/tools/builtin.py:390-399`, `:463-472`;
`backend/open_webui/utils/middleware.py:1883-1888`, `:1991-1996`). That is why the comment in
`backend/open_webui/routers/images.py:860-863` says the internal callers "gate themselves".

Two client functions, `getImageGenerationConfig` and `updateImageGenerationConfig`, call
`/api/v1/images/image/config` and `/image/config/update`, which do not exist in the router; the
admin panel imports them but never calls them (`src/lib/apis/images/index.ts:106-169`;
`src/lib/components/admin/Settings/Images.svelte:8-15`). `ResponseMessage.svelte` also imports
`imageGenerations` without using it (`src/lib/components/chat/Messages/ResponseMessage.svelte:29`).

## 3. Roles and Permissions

### 3.1 Roles

| Role | Can use image generation | Can configure it | Playground | Source |
|---|---|---|---|---|
| `admin` | Yes when the admin switch is on; admins skip the `features.image_generation` permission check at every call site | Yes | Yes | `backend/open_webui/routers/images.py:271-277`, `:571-573`, `:871-873`; `backend/open_webui/utils/tools.py:559-566`; `backend/open_webui/utils/middleware.py:2713` |
| `user` | When the admin switch is on and the permission allows it (3.2) | No | Not offered in the menu; the page sends non-admins to `/` | `src/lib/components/playground/Images.svelte:115-121`; `src/lib/components/layout/Sidebar/UserMenu.svelte:425` |
| `pending` | No: every image route needs a verified user, and pending accounts are refused | No | No | `backend/open_webui/routers/images.py:34`, `:363`, `:563`, `:859`; ground truth (role checks answer 401) |

Admins are **not** exempt from the admin switches: with **Image Generation** off, an admin also
gets no image toggle and `POST /generations` refuses them
(`backend/open_webui/routers/images.py:565-569`; `src/lib/components/chat/MessageInput.svelte:831-834`).

### 3.2 Every Gate Between a User and a Picture

All of the following must allow it. The first failing gate decides what the user sees.

| # | Gate | Set by | Code default | When it blocks | Source |
|---|---|---|---|---|---|
| 1 | **Image Generation** switch (`image_generation.enable`) | Admin, Images tab | **off** | No image toggle in the composer (the browser only learns this switch, as `features.enable_image_generation`); `generate_image` not offered; `POST /generations` answers 403 `ACCESS_PROHIBITED`; the legacy step does nothing unless it is editing | `backend/open_webui/config.py:1351`, `:3019`; `backend/open_webui/main.py:2367`; `backend/open_webui/utils/tools.py:689-696`; `backend/open_webui/routers/images.py:565-569`; `backend/open_webui/utils/middleware.py:1866-1868` |
| 2 | **Image Edit** switch (`images.edit.enable`) | Admin, Images tab | **off** | `edit_image` not offered; `POST /edit` answers 403; in legacy mode pictures already in the chat are ignored and a new picture is made instead | `backend/open_webui/config.py:1525`, `:3039`; `backend/open_webui/utils/tools.py:697-704`; `backend/open_webui/routers/images.py:865-869`; `backend/open_webui/utils/middleware.py:1866` |
| 3 | Feature permission `features.image_generation` (switch `Image Generation` under **Features Permissions**) | Admin, default permissions or a group | **on** (`USER_PERMISSIONS_FEATURES_IMAGE_GENERATION`) | No toggle; tools not offered; legacy step skipped even if the browser sends the feature; both routes answer 403 | `backend/open_webui/config.py:1910-1912`, `:2010`; `backend/open_webui/utils/middleware.py:2711-2717`; `backend/open_webui/routers/images.py:571-577`, `:871-877`; `src/lib/components/admin/Users/Groups/Permissions.svelte:1061-1078` |
| 4 | Model capability **Image Generation** (`capabilities.image_generation`, description `Model can generate images based on text prompts`) | Model editor | on when not set | The toggle is hidden unless **every** selected model has it; the native tools are not offered | `src/lib/components/chat/MessageInput.svelte:759-763`, `:783-787`, `:831-834`; `backend/open_webui/utils/tools.py:533-534`, `:691`; `translation.json:2583-2584` |
| 5 | Model **Builtin Tools › Image Generation** group (description `Generate and edit images`) | Model editor | on when not set | Native tools not offered; the composer toggle still shows | `backend/open_webui/utils/tools.py:538-540`, `:689`; `src/lib/components/workspace/Models/BuiltinTools.svelte:53-56`; `translation.json:2552-2553` |
| 6 | Native built-in tools as a whole (the model's **Builtin Tools** capability and the **Function Calling** mode) | Model editor; chat or model parameters | native mode, capability on | Covered in `builtin-native-tools.md` section 3; in `legacy` mode the tools are not used and the legacy step of section 5.6 runs instead | `backend/open_webui/utils/middleware.py:2718-2720`; `builtin-native-tools.md` |
| 7 | The composer switch for this message | The user | off, unless the model's **Default Features › Image Generation** is ticked or the link has `?image-generation=true` | Nothing image-related happens for that message | `src/lib/components/chat/Chat.svelte:1083-1090`, `:2176-2178`, `:3397-3402` |

A group permission can add the permission but cannot take away a permission the defaults grant
(ground truth; `src/lib/components/admin/Users/Groups/Permissions.svelte:1071-1077` shows `This is
a default user permission and will remain enabled.` in that case).

There is **no separate permission for editing**: `POST /edit`, `edit_image` and the legacy edit all
check `features.image_generation` (`backend/open_webui/routers/images.py:871-873`;
`backend/open_webui/utils/tools.py:702`). In chat, editing is reached only through the image
toggle, and the toggle depends on the **Image Generation** switch, so in practice chat editing
needs both switches on (`src/lib/components/chat/Chat.svelte:3399-3402`). The playground's edit
needs only **Image Edit** (`backend/open_webui/routers/images.py:865`).

### 3.3 What Governs the Playground's Image Routes

The playground page is offered to admins only and sends anyone else to `/`
(`src/lib/components/playground/Images.svelte:115-121`). The two routes it calls are governed by
gates 1 to 3 above (the switches and the `features.image_generation` permission), not by the
admin role (`backend/open_webui/routers/images.py:562-577`, `:858-877`), so the permission is the
setting that decides who may create or edit pictures.

### 3.4 Who Can See a Generated Picture

A generated picture is an ordinary file record owned by the person whose request produced it
(`backend/open_webui/routers/images.py:520-537`; section 6). `GET /api/v1/files/{id}/content`
serves it to:

| Who | Why | Source |
|---|---|---|
| The owner | Owns the file | `backend/open_webui/routers/files.py:810` |
| Any admin | Role check | `backend/open_webui/routers/files.py:810` |
| Members of a channel the picture was made in | The file is added to the channel | `backend/open_webui/routers/files.py:430-433`; `backend/open_webui/socket/main.py:1103-1124`; `backend/open_webui/utils/access_control/files.py:66-69` |
| People with read access to a shared chat that is linked to the file | A `chat_file` row joins the file to a chat that has a share link | `backend/open_webui/utils/access_control/files.py:71-83`; `backend/open_webui/models/chats.py:2656-2664` |

The legacy step links each picture to its chat and message in `chat_file`
(`backend/open_webui/routers/images.py:539-551`). The native tools save the picture into the
message's file list instead and pass no chat id to the upload, so no `chat_file` row is written for
them (`backend/open_webui/tools/builtin.py:390-412`, `:463-485`). Whether people viewing a shared
copy of such a chat can load those pictures is **TO BE CONFIRMED** (section 14).

## 4. Key Concepts and Terminology

### 4.1 Glossary

| Term | Meaning here | Source |
|---|---|---|
| **Image engine** | The outside service that actually makes the picture. One engine is chosen for creating (`image_generation.engine`) and a separate one for editing (`images.edit.engine`); both default to `openai` | `backend/open_webui/config.py:1353`, `:1527` |
| **Default (Open AI)** | The label of the `openai` engine. It means "the OpenAI images interface", which other providers also offer; the address is the **API Base URL** setting | `src/lib/components/admin/Settings/Images.svelte:328`, `:387-417` |
| **Image toggle** | The composer switch `Image` (tooltip `Generate an image`). It is sent with the message as `features.image_generation`; on its own it creates nothing, it lets the pipeline or the model do so | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:471-494`; `src/lib/components/chat/Chat.svelte:3393-3410` |
| **Native mode** (default) | The model is given the `generate_image` and `edit_image` tools and decides itself whether and when to call them, and with what prompt | `backend/open_webui/utils/tools.py:687-704`; `builtin-native-tools.md` |
| **Legacy mode** | The chat's **Function Calling** parameter is `legacy`. MedIT GPT then makes (or edits) the picture **before** the model answers and tells the model the outcome in a hidden note | `backend/open_webui/utils/middleware.py:2718-2720`, `:1828-2046` |
| **Image prompt** | The text sent to the engine. In legacy mode it is the user's last message, or, when **Image Prompt Generation** is on, a description written by the task model from the last six messages. In native mode it is whatever the model passes to the tool | `backend/open_webui/utils/middleware.py:1851-1853`, `:1950-1988`; `backend/open_webui/config.py:2256-2274` |
| **Task model** | The model that runs background tasks such as titles; it also writes image prompts (`chat-completion-pipeline-and-generation-tasks.md`) | `backend/open_webui/routers/tasks.py:359` |
| **Model (image)** | Which picture model the engine uses: a name such as `dall-e-3` or `gpt-image-1` for OpenAI-style services, an Imagen or Gemini model name for Gemini, a checkpoint file for ComfyUI and Automatic1111 | `backend/open_webui/routers/images.py:202-225`, `:362-433` |
| **Checkpoint** | A model file loaded by a Stable Diffusion server (ComfyUI or Automatic1111); Automatic1111 keeps **one** loaded for the whole server | `backend/open_webui/routers/images.py:795-800` |
| **Size** | Width x height in pixels, written like `512x512`; `auto` is accepted only for models matching `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN` (default `^gpt-image`) | `backend/open_webui/routers/images.py:278-293`; `backend/open_webui/config.py:1358`, `:1363` |
| **Steps** | How many refinement rounds a Stable Diffusion engine runs (ComfyUI, Automatic1111); not used by OpenAI or Gemini | `backend/open_webui/routers/images.py:747-748`, `:809-810`; `src/lib/components/admin/Settings/Images.svelte:363-372` |
| **ComfyUI workflow** | A JSON description of a ComfyUI processing graph, exported from ComfyUI in **API format**, uploaded on the Images tab. There is one for creating and an optional one for editing | `translation.json:2426-2427`; `backend/open_webui/config.py:1384-1495`, `:1547` |
| **Workflow nodes** (node mapping) | For each kind of value MedIT GPT fills in (prompt, model, width, height, steps, seed; for edits image, prompt, model, width, height), the **input key** and the **node ids** in the workflow that receive it | `src/lib/components/admin/Settings/Images.svelte:41-101`, `:642-690`; `backend/open_webui/utils/images/comfyui.py:147-186` |
| **Gemini endpoint method** | `predict` (Imagen-style request and answer) or `generateContent` (Gemini-style); blank means `predict` | `backend/open_webui/routers/images.py:689-704`; `src/lib/components/admin/Settings/Images.svelte:716-727` |
| **Additional Parameters** | Extra JSON fields merged into every OpenAI-style creation request or Automatic1111 request; they can override the built-in ones | `backend/open_webui/routers/images.py:651`, `:815-816`; `translation.json:2419-2420`, `:2464-2465` |
| **API Version** | Added to OpenAI-style requests as `?api-version=...` when set; which providers need it is outside the code | `backend/open_webui/routers/images.py:631-632`, `:1014-1016` |
| **Edit normalization** | Before an OpenAI-style edit, JPEG pictures that are multi-frame, rotated by camera metadata or not plain RGB are rewritten as plain JPEG; on by default (`ENABLE_OPENAI_IMAGE_EDIT_NORMALIZATION`) | `backend/open_webui/routers/images.py:118-154`, `:1005-1011`; `backend/open_webui/config.py:1533` |
| **Generated picture file** | The stored result: a file named `generated-image.<ext>` owned by the requester (section 6) | `backend/open_webui/routers/images.py:520-559` |

### 4.2 Engine Capability Matrix

| | Default (Open AI) | Gemini | ComfyUI | Automatic1111 |
|---|---|---|---|---|
| Create | `POST {API Base URL}/images/generations` | `POST {Base URL}/models/{model}:predict` or `:generateContent` | Queues the workflow on `{Base URL}/prompt` and waits on the server's websocket | `POST {Base URL}/sdapi/v1/txt2img` |
| Edit | `POST {API Base URL}/images/edits` (multipart upload of the pictures) | `POST {Base URL}/models/{model}:generateContent` with the pictures inline | Uploads the pictures to `{Base URL}/api/upload/image`, then runs the edit workflow | Not supported |
| Size sent | The **Image Size** value, or none when blank | **Never** (size is not part of the request) | Width and height into the mapped nodes (512 x 512 when the size is blank or `auto`) | Width and height (512 x 512 when blank or `auto`) |
| Steps sent | No | No | Yes, into the mapped steps node | Yes |
| Number of pictures | `n` (1 from every MedIT GPT screen) | `sampleCount` (`predict` only) | Mapped `n` node, if any | `batch_size` |
| Default model when blank | `dall-e-2` | `imagen-3.0-generate-002` | none (empty) | The checkpoint currently loaded on the server |
| Connection test button | No | No | Yes (`/object_info`) | Yes (`/sdapi/v1/options`) |
| Source | `backend/open_webui/routers/images.py:621-679`, `:978-1057`, `:204-205` | `:681-737`, `:1059-1114`, `:206-207` | `:739-793`, `:1116-1198`; `backend/open_webui/utils/images/comfyui.py:17-119`, `:189-255` | `:794-840`, `:210-225` |

MedIT GPT asks for one picture on every path: `CreateImageForm` defaults `n` to 1 and neither
the chat paths nor the playground set it; edits send no `n` unless given
(`backend/open_webui/routers/images.py:445-451`, `:989`; `src/lib/apis/images/index.ts:213-215`).
An engine can still return more than one, for example a ComfyUI workflow whose own batch size is
larger or **Additional Parameters** that set a count; every returned picture is stored and shown
(`backend/open_webui/routers/images.py:664-679`, `:773-793`, `:828-840`).

### 4.3 Where the Model List Comes From

The **Model** box on the Images tab offers suggestions from `GET /api/v1/images/models`, which
depends only on the **creation** engine (`backend/open_webui/routers/images.py:362-442`;
`src/lib/components/admin/Settings/Images.svelte:103-108`, `:348-352`):

| Creation engine | Suggestions | Source |
|---|---|---|
| Default (Open AI) | A fixed list: `DALL·E 2` (`dall-e-2`), `DALL·E 3` (`dall-e-3`), `GPT-IMAGE 1` (`gpt-image-1`), `GPT-IMAGE 1.5` (`gpt-image-1.5`) | `backend/open_webui/routers/images.py:366-372` |
| Gemini | One entry, `imagen-3.0 generate-002` (`imagen-3.0-generate-002`) | `backend/open_webui/routers/images.py:373-376` |
| ComfyUI | Read from the ComfyUI server: the choices of the mapped model node's first input whose name contains `_name`, or the `CheckpointLoaderSimple` checkpoints when no model node is mapped | `backend/open_webui/routers/images.py:377-419` |
| Automatic1111 | The server's model list (`/sdapi/v1/sd-models`) | `backend/open_webui/routers/images.py:420-433` |

The box accepts any typed value, so a model not in the list can be used. The **edit** model box
shows the same suggestions even when the edit engine is different
(`src/lib/components/admin/Settings/Images.svelte:756-769`). The list is fetched only while
**Image Generation** is switched on (`src/lib/components/admin/Settings/Images.svelte:155-157`, `:236-238`).

## 5. Workflows (Step by Step)

### 5.1 Admin: Switch On Image Generation and Choose an Engine

1. Open the Settings window, **Images** (section 2.1). The panel loads the current values with
   `GET /api/v1/images/config`; if that fails the server's text is shown in a red pop-up and the
   panel stays empty (`src/lib/components/admin/Settings/Images.svelte:221-234`).
2. Turn on **Image Generation** (`Allow users to generate images from prompts.`). While it is on,
   the panel shows **Model**, **Image Size**, **Steps** (ComfyUI and Automatic1111 only) and
   **Image Prompt Generation** (`src/lib/components/admin/Settings/Images.svelte:310-385`;
   `translation.json:2441-2447`, `:2461`, `:2470`).
3. Choose the **Image Generation Engine** (`Choose the provider used for image generation.`):
   `Default (Open AI)`, `ComfyUI`, `Automatic1111` or `Gemini`
   (`src/lib/components/admin/Settings/Images.svelte:320-333`; `translation.json:2443-2444`).
4. Fill in the engine's connection fields (section 7.1). For Automatic1111 and ComfyUI the
   circular-arrow button (accessible name `verify connection`) tests the address and shows
   `Server connection verified` on success (`src/lib/components/admin/Settings/Images.svelte:441-460`,
   `:512-531`; `translation.json:2469`, `:2472`).
5. Enter or pick a **Model** (required while Image Generation is on; the browser blocks saving an
   empty box with its own prompt) and, if wanted, an **Image Size** such as `1024x1024` and
   **Steps** (`src/lib/components/admin/Settings/Images.svelte:337-372`).
6. Press **Save**. In order:
   1. The browser checks the engine's required field and, if it is empty, shows one of
      `AUTOMATIC1111 Base URL is required.`, `ComfyUI Base URL is required.`,
      `OpenAI API Key is required.` or `Gemini API Key is required.`, flips the **Image
      Generation** switch back off in the form and saves nothing. This check runs even when the
      switch is off (`src/lib/components/admin/Settings/Images.svelte:110-134`).
   2. Workflow text, if any, must be valid JSON (`Invalid JSON format for ComfyUI Workflow.`,
      `Invalid JSON format for ComfyUI Edit Workflow.`), and the node mappings are rebuilt from
      the form (`:176-211`).
   3. The two **Additional Parameters** boxes are read as JSON (`:136-146`).
   4. The server checks size and steps (section 7.2), saves all 33 settings, applies the model and
      records a `config.updated` event (`backend/open_webui/routers/images.py:276-319`).
   5. The browser reloads the site settings for the admin's own page and shows
      `Settings saved successfully!` (`src/lib/components/admin/Settings/Images.svelte:152-157`,
      `:213-216`; `src/lib/components/chat/SettingsModal.svelte:891-896`).
7. Other people's browsers read the switch and their permissions when MedIT GPT loads
   (`src/routes/+layout.svelte:1240`, `:1280-1292`), so a page that is already open may need a
   reload before the image toggle appears.

Saving the form at all requires the selected creation engine's key or address, even when the admin
only wants to change editing settings (step 6.1).

### 5.2 Admin: Set Up Image Editing

1. In the **Edit Image** section turn on **Image Edit** (`Allow users to edit existing images.`)
   and choose the **Image Edit Engine** (`Choose the provider used for image edits.`):
   `Default (Open AI)`, `ComfyUI` or `Gemini` (`src/lib/components/admin/Settings/Images.svelte:731-752`;
   `translation.json:2435-2438`).
2. **Model** and **Image Size** for edits are shown only when **both** switches are on
   (`src/lib/components/admin/Settings/Images.svelte:754-779`). Unlike creation, a blank edit
   model is sent to the engine as an empty name: there is no fallback
   (`backend/open_webui/routers/images.py:913`).
3. Fill in the edit engine's own address and key (section 7.1). The edit engine has separate
   fields from the creation engine even when both are the same kind
   (`src/lib/components/admin/Settings/Images.svelte:781-1018`).
4. For ComfyUI, upload an edit workflow and map its nodes (5.3).
5. Press **Save** (5.1 step 6).

### 5.3 Admin: Configure ComfyUI Workflows and Node Mapping

1. Build the workflow in ComfyUI and export it in API format (`Upload a workflow.json file
   exported as API format from ComfyUI.`, `translation.json:2426`).
2. On the Images tab click **Upload** (tooltip `Click here to upload a workflow.json file.`) and
   choose the `.json` file; **Edit** opens the text in a code editor
   (`src/lib/components/admin/Settings/Images.svelte:561-640`; `translation.json:2421`, `:2430`).
   If no workflow is uploaded for creation, the built-in default workflow is used (below).
3. Under **ComfyUI Workflow Nodes** (`Map workflow node inputs used for image generation.`), for each
   row enter the input **Key** and the comma-separated **Node Ids** (tooltips
   `Input Key (e.g. text, unet_name, steps)` and `Comma separated Node Ids (e.g. 1 or 1,2)`). The
   note under the rows reads `*Prompt node ID(s) are required for image generation`
   (`src/lib/components/admin/Settings/Images.svelte:642-690`; `translation.json:2433-2434`).
4. Save. Only the rows shown on the form are kept: creation rows `prompt`, `model`, `width`,
   `height`, `steps`, `seed`; edit rows `image`, `prompt`, `model`, `width`, `height`
   (`src/lib/components/admin/Settings/Images.svelte:41-101`, `:186-210`).

What the server does with the mapping (`backend/open_webui/utils/images/comfyui.py:147-186`):

| Row | Value written into each listed node's input | Default key if blank |
|---|---|---|
| `prompt` | The image prompt | `text` |
| `negative_prompt` | The negative prompt (not set by any MedIT GPT screen; mapping only through `COMFYUI_WORKFLOW_NODES`) | `text` |
| `model` | The configured model name | the key as entered (form default `ckpt_name`, edit form default `unet_name`) |
| `width`, `height` | From the size (5.11) | `width`, `height` |
| `steps` | **Steps** | `steps` |
| `seed` | A new random number for every picture (no screen sets a seed) | the key as entered (form default `seed`) |
| `n` | Number of pictures (1 on every MedIT GPT path; mapping only through `COMFYUI_WORKFLOW_NODES`) | `batch_size` |
| `image` (edit) | The uploaded source picture names, first picture to the first node id, and so on | the key as entered (form default `image`) |
| a row with no type | The row's fixed `value` (only through the environment variables) | — |

A row with no node ids changes nothing. A node id that is not in the workflow makes the request
fail (`Something went wrong :/`, section 10.2). Only pictures from `SaveImage` and
`PreviewImage` nodes are collected; for edits, pictures whose address says `type=output` are
preferred over the others when there are any
(`backend/open_webui/utils/images/comfyui.py:89-100`; `backend/open_webui/routers/images.py:1166-1174`).

The built-in default workflow (`backend/open_webui/config.py:1384-1493`) is a basic text-to-image
graph. Its node ids, which a mapping for it would use, are:

| Node id | Node type | Inputs of interest | Line |
|---|---|---|---|
| `3` | `KSampler` | `seed` (0), `steps` (20) | `backend/open_webui/config.py:1386-1411` |
| `4` | `CheckpointLoaderSimple` | `ckpt_name` (`model.safetensors`) | `:1416-1420` |
| `5` | `EmptyLatentImage` | `width` 512, `height` 512, `batch_size` 1 | `:1425-1431` |
| `6` | `CLIPTextEncode` | `text` (`Prompt`, the positive prompt) | `:1436-1444` |
| `7` | `CLIPTextEncode` | `text` (empty, the negative prompt) | `:1449-1457` |
| `9` | `SaveImage` | `filename_prefix` `ComfyUI` | `:1478-1486` |

`COMFYUI_WORKFLOW_NODES` defaults to an empty list (`backend/open_webui/config.py:1497-1503`), so
until an admin maps at least the prompt row, the default workflow draws its literal placeholder
text instead of the user's request.

### 5.4 User: Create a Picture in a Chat (Native Mode, the Default)

1. Start or open a chat with a model that has the **Image Generation** capability (3.2).
2. Click **Integrations** and turn on **Image**; the blue picture chip appears
   (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:471-494`;
   `src/lib/components/chat/MessageInput.svelte:2502-2519`).
3. Describe the picture and send. The browser sends `features.image_generation: true`
   (`src/lib/components/chat/Chat.svelte:3393-3410`).
4. The server offers the model `generate_image` (when **Image Generation** is on) and `edit_image`
   (when **Image Edit** is on) (`backend/open_webui/utils/tools.py:687-704`).
5. The model decides whether to call `generate_image` and writes the prompt itself. The call
   appears in the reply as a tool entry (`builtin-native-tools.md` sections 4.2 and 5.6).
6. The server calls the creation engine (5.10), saves the picture as a file, adds it to the reply's
   files and pushes it to the page with a `chat:message:files` event
   (`backend/open_webui/tools/builtin.py:390-423`).
7. The model is told `The image has been successfully generated and is already visible to the user
   in the chat. You do not need to display or embed the image again - just acknowledge that it has
   been created.` and normally confirms in words (`backend/open_webui/tools/builtin.py:425-432`).

If the engine fails, the tool returns `{"error": "..."}` to the model, which usually explains the
failure in its reply; nothing else is shown (`backend/open_webui/tools/builtin.py:435-437`). The
toggle stays on for later messages until the user turns it off.

### 5.5 User: Edit a Picture in a Chat

1. Attach the picture to the message (the ways to attach are in
   `chat-composer-and-message-display.md`). Attaching a picture needs at least one selected
   model with the **Vision** capability (`Model accepts image inputs`), otherwise the composer
   says `Selected model(s) do not support image inputs`
   (`src/lib/components/chat/MessageInput.svelte:1126-1130`; `translation.json:2594-2595`). A
   picture generated earlier in the chat can also be the source.
2. Turn on **Image** (5.4 step 2) and describe the change ("make the sky orange").
3. **Native mode:** the model may call `edit_image` with the source picture addresses it can see
   in the conversation, such as the address returned by an earlier `generate_image`; the tool
   accepts inline pictures, `/api/v1/files/{id}/content` paths, bare file ids and web links
   (`backend/open_webui/tools/builtin.py:440-472`; `backend/open_webui/routers/images.py:917-961`).
   Which addresses a given model reliably passes is TO BE CONFIRMED (section 14).
4. **Legacy mode:** MedIT GPT edits automatically whenever the conversation already contains
   pictures and **Image Edit** is on (5.6).
5. The edited picture is saved and shown like a created one; the model is told
   `The edited image has been successfully generated and is already visible to the user in the
   chat. You do not need to display or embed the image again - just acknowledge that it has been
   created.` (`backend/open_webui/tools/builtin.py:498-505`).

When a message is sent in a chat that contains pictures to a model without the **Vision**
capability, the chat page shows the (non-blocking) warning `Model {{modelName}} is not vision
capable`, except while the image toggle is on (`src/lib/components/chat/Chat.svelte:3336-3357`).

### 5.6 What the Server Does in Legacy Mode

When the chat's **Function Calling** is `legacy` and the image feature arrives with the message,
`chat_image_generation_handler` runs before the model is called
(`backend/open_webui/utils/middleware.py:2711-2720`, `:1828-2046`):

1. It needs a chat id and an event channel to the browser; otherwise it does nothing
   (`:1833-1834`).
2. It takes the conversation (from the database for saved chats, from the request for temporary
   chats and channels) and the **last user message** as the prompt (`:1842-1853`).
3. It collects pictures from the two most recent messages that have any, of either role,
   including pictures the assistant generated earlier (`:1854-1863`, `:1733-1747`).
4. **Edit or create?** If pictures were found **and** **Image Edit** is on, it edits them; if not,
   and **Image Generation** is off, it stops silently (`:1865-1868`).
5. For saved chats it shows the status `Creating image` (`:1870-1876`).
6. **Edit:** calls the edit engine with the user's words and the pictures (`:1880-1888`).
   **Create:** first, when **Image Prompt Generation** is on, asks the task model for a better
   prompt (5.7), then calls the creation engine (`:1948-1996`).
7. On success it shows `Image created`, sends the pictures to the page with a `files` event (the
   server also saves them on the message) and adds a hidden note for the model, for example
   `<context>The requested image has been created by the system successfully and is now being shown
   to the user. Let the user know that the image they requested has been generated and is now shown
   in the chat.</context>` (`:1890-1912`, `:1998-2020`; `backend/open_webui/socket/main.py:1220-1233`).
8. On failure it shows `An error occurred while generating an image` and tells the model the error
   text so that it can explain it (`:1913-1933`, `:2021-2041`).
9. The model then writes its reply as usual (`:2043-2046`).

Consequence: in legacy mode, once a chat contains a picture, every later message with the image
toggle on becomes an **edit** of the most recent pictures (when Image Edit is on), even if the user
asked for something new. Starting a new chat avoids that.

### 5.7 Image Prompt Generation (Legacy Mode Only)

With **Image Prompt Generation** on (`Generate an image prompt before sending the request.`, code
default on, `ENABLE_IMAGE_PROMPT_GENERATION`), the legacy create path asks the task model for a
detailed description before calling the engine (`backend/open_webui/utils/middleware.py:1950-1988`;
`backend/open_webui/config.py:1367`; `translation.json:2446-2447`):

1. The template is **Image Prompt Generation Prompt** (`task.image.prompt_template`) or, when
   blank, the built-in template that asks for a description "as if you were explaining it to
   someone who cannot see it" and a JSON answer `{"prompt": ...}`, using the last six messages
   (`backend/open_webui/routers/tasks.py:365-371`; `backend/open_webui/config.py:2256-2274`).
2. The task model is chosen as for other background tasks
   (`backend/open_webui/routers/tasks.py:359`; `chat-completion-pipeline-and-generation-tasks.md`).
3. The server takes the text from the last `{` to the last `}` of the answer and reads its
   `prompt` field. If the task call fails or that text is not JSON, the user's own last message is
   used instead, without telling the user (`backend/open_webui/utils/middleware.py:1962-1988`).
   Derived from the code, not observed: JSON without a `prompt` field leaves an empty list as the
   prompt, which the creation step rejects, so the user sees `An error occurred while generating an
   image` (`:1982`, `:1990-1996`, `:2021-2041`).

Native mode does not use this setting: the chat model writes the prompt in its tool call
(`backend/open_webui/tools/builtin.py:370-392`). Edits never use it
(`backend/open_webui/utils/middleware.py:1880-1888`).

### 5.8 Admin: Use the Images Playground

1. Profile menu › **Playground** › **Images** (`/playground/images`).
2. Type a description in the box (placeholder `Describe the image...`).
3. Optional, to edit: **Add Image** (or drop picture files on the button); thumbnails appear with a
   remove button (`Remove image`) and the placeholder changes to `Describe the edit...`
   (`src/lib/components/playground/Images.svelte:30-65`, `:182-232`, `:246-254`).
4. Press **Run** or **Ctrl/Cmd+Enter**. The button shows `Running...` while waiting
   (`:225-230`, `:257-274`).
5. Without source pictures the page calls `POST /api/v1/images/generations`; with one or more it
   calls `POST /api/v1/images/edit` with all of them (`:67-98`).
6. Results are added to the front of the grid (`Generated images will appear here` until the
   first one). Clicking a picture downloads it as `image-{Date.now()}-{index}.png`, whatever its real type
   (`:100-113`, `:134-171`).
7. Errors appear in a red pop-up with the server's text (`:92-95`). An empty prompt gives
   `Please enter a prompt` (`:67-71`).

Nothing on the page is kept after leaving it, but every result is still saved as a file record
owned by the admin, with no chat link (section 6; `backend/open_webui/routers/images.py:520-559`).
The playground uses the admin-configured model and size; it offers no model, size or count
choice (`src/lib/apis/images/index.ts:203-240`, `:242-292`).

### 5.9 Channels and Automations

When a model is mentioned in a channel, or an automation runs, the model's **Default Features**
supply the image feature if the model has the **Image Generation** capability and the admin switch
is on (`backend/open_webui/utils/automations.py:166-199`; `backend/open_webui/routers/channels.py:1103-1129`).
In a channel the picture is added to the channel's files, so channel members can see it
(`backend/open_webui/routers/files.py:430-433`; `backend/open_webui/socket/main.py:1103-1124`).
The legacy `Creating image` status is shown only for saved chats, not in channels
(`backend/open_webui/utils/middleware.py:1870-1876`). Details are in
`channels-and-direct-messages.md`.

### 5.10 From Engine Answer to Stored File

For every engine the result is handled the same way (`backend/open_webui/routers/images.py:479-559`):

1. The picture arrives either as inline data or as a link. Links are downloaded by the server; a
   link must point at a picture (`content-type` beginning `image/`), otherwise it is dropped with
   the log line `Url does not point to an image.` (`:479-517`). Links are subject to the same
   address-safety check as web loading unless they come from the configured engine's own address
   (`:489-492`; `web-search-and-web-loading.md`).
2. The bytes are uploaded through the normal file upload path without content processing, as a
   file named `generated-image.<ext>` (`:520-537`). The site's maximum upload size still applies
   (`backend/open_webui/routers/files.py:394-400`).
3. For legacy chats the file is linked to the chat and message (`chat_file`) (`:539-551`).
4. The caller receives `{id, url, name, content_type}`, where `url` is
   `/api/v1/files/{id}/content` (`:553-559`).

### 5.11 Size, Steps and Model: Which Value Wins

| Value | Creation | Edit | Source |
|---|---|---|---|
| Size | The admin's **Image Size**. No MedIT GPT screen or tool sends a size of its own. OpenAI-style: sent as written (including `auto`), or left out when blank. ComfyUI and Automatic1111: used for width and height when it contains an `x`, otherwise 512 x 512. Gemini: not sent | **Image Size** under Edit Image; sent only when it contains an `x` (OpenAI-style and ComfyUI); Gemini: not sent | `backend/open_webui/routers/images.py:603-614`, `:638-642`, `:903-911`, `:990`, `:1141-1142` |
| Steps | **Steps** (ComfyUI and Automatic1111) | Not used | `backend/open_webui/routers/images.py:747-748`, `:809-810` |
| Model | The admin's **Model**; for OpenAI-style, Gemini and ComfyUI the request's own model field is ignored. For Automatic1111 an **admin's** request that names a model switches the server's checkpoint for everyone; other users' model choices are ignored | The admin's edit **Model**, unless the caller names one (no MedIT GPT screen does); no default | `backend/open_webui/routers/images.py:618`, `:795-800`, `:913` |
| Extra parameters | **Additional Parameters** override anything above for OpenAI-style and Automatic1111 creation | None | `backend/open_webui/routers/images.py:651`, `:815-816` |

The engine may still return a different size from the one asked for; MedIT GPT does not check or
resize the result (`backend/open_webui/routers/images.py:664-679`).

### 5.12 Waiting and Time Limits

There is no image-specific time limit. Outside requests use the shared connection pool, whose
overall limit is `AIOHTTP_CLIENT_TIMEOUT`, unset (no limit) by default
(`backend/open_webui/utils/session_pool.py:43-79`; `backend/open_webui/env.py:608-612`). ComfyUI
jobs wait on the ComfyUI websocket until ComfyUI reports the job finished or closes the connection
(`backend/open_webui/utils/images/comfyui.py:69-100`). A slow or queued engine therefore keeps
`Creating image`, the tool entry or `Running...` on screen until the engine answers. Limits set by
a proxy in front of MedIT GPT are TO BE CONFIRMED (section 14).

## 6. Data Model

Image generation has **no table of its own**. A generated or edited picture becomes an ordinary
uploaded file; the general file model is documented in `files-uploads-and-storage.md`
(sections 6.1 to 6.3 there). This section covers only what is specific to pictures.

### 6.1 What Is Written for Each Picture

| Store | What | Source |
|---|---|---|
| Storage provider (default `DATA_DIR/uploads`, or S3, GCS, Azure per `STORAGE_PROVIDER`) | The picture bytes, stored as `{id}_generated-image.{ext}` (or `{id}.{ext}` if the name is rejected). The owner's email, id and name and the file id are passed as storage tags, which only S3 storage with `S3_ENABLE_TAGGING` keeps | `backend/open_webui/routers/images.py:523-537`; `backend/open_webui/routers/files.py:364-393`; `backend/open_webui/storage/provider.py:145-157` |
| `file` table, one row | `id`; `user_id` = the requester; `filename` and `meta.name` = `generated-image.{ext}`; `meta.content_type`; `meta.size`; `meta.file_hash`; `meta.data` = the request sent to the engine plus the chat or channel ids (6.2); `data` empty (no content processing) | `backend/open_webui/routers/files.py:408-428`; `backend/open_webui/routers/images.py:531-537` |
| `chat_file` table, one row (legacy path only) | Links the file to `chat_id` and `message_id` | `backend/open_webui/routers/images.py:539-551`; `backend/open_webui/models/chats.py:217-228` |
| `channel_file` link (channel requests only) | Adds the file to the channel | `backend/open_webui/routers/files.py:430-433`; `backend/open_webui/models/channels.py:158`, `:853` |
| The chat's JSON (`chat.chat.history.messages[{message_id}].files`) | An entry `{type: 'image', id, url, name, content_type}` appended to the assistant message | `backend/open_webui/tools/builtin.py:402-412`; `backend/open_webui/models/chats.py:1274-1306`; `backend/open_webui/socket/main.py:1220-1233` |

The file's extension comes from the content type the engine returned
(`backend/open_webui/routers/images.py:523`). The file name does not contain the prompt.

### 6.2 What `meta.data` Holds, by Engine

Because the request is copied into the file record, **the prompt is stored with every picture**,
and for some engines more (`backend/open_webui/routers/images.py:677`, `:721`, `:728-734`,
`:785-791`, `:832-838`, `:1055`, `:1105-1111`, `:1189-1195`):

| Engine and action | Copied into `meta.data` |
|---|---|
| OpenAI-style, create | `model`, `prompt`, `n`, `size` (if any), `response_format` (if sent) and the **Additional Parameters** |
| OpenAI-style, edit | `model`, `prompt`, and `n`, `size`, `background`, `response_format` when sent |
| Gemini, create | The request body: the prompt and, for `predict`, the sample count and output type |
| Gemini, edit | The request body, which contains the prompt **and the full source pictures** as inline data |
| ComfyUI, create or edit | The prompt, sizes and steps, the source picture names for edits, and the **whole workflow** text and node mapping |
| Automatic1111 | The prompt, width, height, steps, batch size, the **Additional Parameters** and the engine's `info` answer |
| All | `chat_id` (legacy) or `channel_id`, and `message_id`, when the request came from a chat or channel |

Engine keys travel in request headers and are not part of `meta.data`
(`backend/open_webui/routers/images.py:622-628`, `:682-685`, `:979-984`, `:1060-1063`).

### 6.3 Lifetime

Nothing in the image code deletes a picture. Deleting the chat or the user leaves the file
(`files-uploads-and-storage.md`; ground truth); the owner can delete it from their files list, as
with any upload (`files-uploads-and-storage.md` section 11.10). Pictures made in the playground are
kept as files although the page forgets them (section 5.8).

### 6.4 The `cache/image/generations` Folder

The images router creates `DATA_DIR/cache/image/generations/` when the server starts
(`backend/open_webui/routers/images.py:54-55`), but no code in v0.11.4 reads or writes that folder;
pictures go to the storage provider instead (6.1). The folder may hold pictures from older
releases; whether it does here is TO BE CONFIRMED (section 14).

### 6.5 Settings Rows

The 33 image settings are rows in the `config` table, one per dotted key (section 7.1); the values
are data (ground truth). There is no per-user image setting.

## 7. Settings and Configuration

All 33 image settings are persistent: after the first start the value stored in the `config` table
wins over the environment variable (ground truth). The environment variable only seeds the first
value. Live values are data: **TO BE CONFIRMED** for production. Keys and secrets are cited by
location only.

### 7.1 Admin Settings › Images, Field by Field

Labels are dotted keys resolved in `src/lib/i18n/locales/en-US/translation.json:2415-2472`; all
config lines are in `backend/open_webui/config.py`, with the persistent key listed at `:3019-3051`.

**Create Image section**

| Label (description) | Key | Environment variable | Code default | Shown when | Notes | Source |
|---|---|---|---|---|---|---|
| **Image Generation** (`Allow users to generate images from prompts.`) | `image_generation.enable` | `ENABLE_IMAGE_GENERATION` | off | always | Gate 1 of 3.2 | `:1351`, `:3019`; `Images.svelte:310-316` |
| **Image Generation Engine** (`Choose the provider used for image generation.`) | `image_generation.engine` | `IMAGE_GENERATION_ENGINE` | `openai` | always | Options `Default (Open AI)`, `ComfyUI`, `Automatic1111`, `Gemini`. An empty stored value is treated as Automatic1111 | `:1353`, `:3020`; `Images.svelte:320-333`; `images.py:210`, `:420`, `:794` |
| **Model** (placeholder `Select a model`) | `image_generation.model` | `IMAGE_GENERATION_MODEL` | empty | switch on | Required on the form; blank falls back per engine (4.2) | `:1355`, `:3021`; `Images.svelte:337-353` |
| **Image Size** (placeholder `Enter Image Size (e.g. 512x512)`) | `image_generation.size` | `IMAGE_SIZE` | `512x512` | switch on | `WIDTHxHEIGHT`, blank, or `auto` (7.2) | `:1363`, `:3022`; `Images.svelte:355-361` |
| **Steps** (placeholder `Enter Number of Steps (e.g. 50)`) | `image_generation.steps` | `IMAGE_STEPS` | `50` | switch on and engine ComfyUI or Automatic1111 | Required on the form when shown | `:1365`, `:3023`; `Images.svelte:363-372` |
| **Image Prompt Generation** (`Generate an image prompt before sending the request.`) | `image_generation.prompt.enable` | `ENABLE_IMAGE_PROMPT_GENERATION` | **on** | switch on | Legacy mode only (5.7) | `:1367`, `:3024`; `Images.svelte:375-384` |
| **API Base URL** (OpenAI-style) | `image_generation.openai.api_base_url` | `IMAGES_OPENAI_API_BASE_URL` | `OPENAI_API_BASE_URL`, which is `https://api.openai.com/v1` when unset | engine `openai` | Requests go to `{this}/images/generations` | `:1505`, `:3032`, `:328-333`; `Images.svelte:389-397` |
| **API Key** (OpenAI-style) | `image_generation.openai.api_key` | `IMAGES_OPENAI_API_KEY` | the value of `OPENAI_API_KEY` | engine `openai` | Masked field; the browser refuses to save when empty (`OpenAI API Key is required.`) | `:1508`, `:3034`; `Images.svelte:399-406`, `:124-128` |
| **API Version** (OpenAI-style) | `image_generation.openai.api_version` | `IMAGES_OPENAI_API_VERSION` | empty | engine `openai` | Added as `?api-version=` when set | `:1506`, `:3033`; `Images.svelte:409-417` |
| **Additional Parameters** (`Send extra JSON parameters with each image generation request.`) | `image_generation.openai.params` | `IMAGES_OPENAI_PARAMS` | `{}` | engine `openai` | JSON object merged into the request | `:1510-1517`, `:3035`; `Images.svelte:419-429` |
| **Base URL** (``Connect to a stable-diffusion-webui server running with the `--api` flag.``) | `image_generation.automatic1111.base_url` | `AUTOMATIC1111_BASE_URL` | empty | engine `automatic1111` | Placeholder `Enter URL (e.g. http://127.0.0.1:7860/)`; verify button | `:1369`, `:3025`; `Images.svelte:430-476` |
| **API Auth String** (`Provide the --api-auth username and password when required.`) | `image_generation.automatic1111.api_auth` | `AUTOMATIC1111_API_AUTH` | empty | engine `automatic1111` | Placeholder `Enter api auth string (e.g. username:password)`; sent as basic authentication | `:1370`, `:3026`; `Images.svelte:478-488`; `images.py:322-329` |
| **Additional Parameters** (`Send extra JSON parameters with each AUTOMATIC1111 request.`) | `image_generation.automatic1111.api_params` | `AUTOMATIC1111_PARAMS` | `{}` | engine `automatic1111` | Merged into every request, overriding prompt, size and steps if it names them | `:1372-1378`, `:3027`; `Images.svelte:490-500`; `images.py:815-816` |
| **Base URL** (`Connect to the ComfyUI server used for generation.`) | `image_generation.comfyui.base_url` | `COMFYUI_BASE_URL` | empty | engine `comfyui` | Slashes trimmed on save; verify button | `:1380`, `:3028`; `Images.svelte:501-547`; `images.py:302` |
| **API Key** (`Use an API key when your ComfyUI server requires one.`) | `image_generation.comfyui.api_key` | `COMFYUI_API_KEY` | empty | engine `comfyui` | Placeholder `sk-1234`; sent as a bearer token | `:1382`, `:3029`; `Images.svelte:549-559` |
| **ComfyUI Workflow** (`Upload a workflow.json file exported as API format from ComfyUI.`) | `image_generation.comfyui.workflow` | `COMFYUI_WORKFLOW` | the built-in default workflow (5.3) | engine `comfyui` | **Upload** and **Edit** buttons | `:1384-1495`, `:3030`; `Images.svelte:561-640` |
| **ComfyUI Workflow Nodes** (`Map workflow node inputs used for image generation.`) | `image_generation.comfyui.nodes` | `COMFYUI_WORKFLOW_NODES` | `[]` | engine `comfyui` and a workflow present | Six rows (5.3) | `:1497-1503`, `:3031`; `Images.svelte:642-690` |
| **Base URL** (`Override the Gemini image generation endpoint.`) | `image_generation.gemini.api_base_url` | `IMAGES_GEMINI_API_BASE_URL` | the value of `GEMINI_API_BASE_URL`, empty by default | engine `gemini` | Despite the description, the code has no built-in address, so it must be filled in | `:1520`, `:3036`, `:326`; `Images.svelte:692-702`; `images.py:708` |
| **API Key** (`Use a Gemini API key for image generation.`) | `image_generation.gemini.api_key` | `IMAGES_GEMINI_API_KEY` | the value of `GEMINI_API_KEY` | engine `gemini` | Sent as the `x-goog-api-key` header; the browser refuses to save when empty (`Gemini API Key is required.`) | `:1521`, `:3037`, `:325`; `Images.svelte:704-714`, `:129-133`; `images.py:682-685` |
| **Gemini Endpoint Method** (`Select the Gemini endpoint method to call.`) | `image_generation.gemini.endpoint_method` | `IMAGES_GEMINI_ENDPOINT_METHOD` | empty (treated as `predict`) | engine `gemini` | `predict` or `generateContent` (placeholder `Select Method`) | `:1523`, `:3038`; `Images.svelte:716-727`; `images.py:689-704` |

**Edit Image section**

| Label (description) | Key | Environment variable | Code default | Shown when | Notes | Source |
|---|---|---|---|---|---|---|
| **Image Edit** (`Allow users to edit existing images.`) | `images.edit.enable` | `ENABLE_IMAGE_EDIT` | off | always | Gate 2 of 3.2 | `:1525`, `:3039`; `Images.svelte:732-738` |
| **Image Edit Engine** (`Choose the provider used for image edits.`) | `images.edit.engine` | `IMAGE_EDIT_ENGINE` | `openai` | always | Options `Default (Open AI)`, `ComfyUI`, `Gemini`. Any other stored value makes edits return no result | `:1527`, `:3040`; `Images.svelte:740-752`; `images.py:977-1198` |
| **Model** | `images.edit.model` | `IMAGE_EDIT_MODEL` | empty | both switches on | No fallback when blank (5.2); suggestions come from the creation engine (4.3) | `:1529`, `:3041`; `Images.svelte:754-769` |
| **Image Size** | `images.edit.size` | `IMAGE_EDIT_SIZE` | empty | both switches on | Not checked on save (7.2) | `:1531`, `:3042`; `Images.svelte:771-777` |
| **API Base URL** (OpenAI-style) | `images.edit.openai.api_base_url` | `IMAGES_EDIT_OPENAI_API_BASE_URL` | `OPENAI_API_BASE_URL` | edit engine `openai` | Requests go to `{this}/images/edits` | `:1535`, `:3043`; `Images.svelte:783-791` |
| **API Key** (OpenAI-style) | `images.edit.openai.api_key` | `IMAGES_EDIT_OPENAI_API_KEY` | the value of `OPENAI_API_KEY` | edit engine `openai` | Masked; not required by the browser | `:1538`, `:3045`; `Images.svelte:793-802` |
| **API Version** (OpenAI-style) | `images.edit.openai.api_version` | `IMAGES_EDIT_OPENAI_API_VERSION` | empty | edit engine `openai` | | `:1536`, `:3044`; `Images.svelte:805-813` |
| **Base URL** (`Connect to the ComfyUI server used for image edits.`) | `images.edit.comfyui.base_url` | `IMAGES_EDIT_COMFYUI_BASE_URL` | empty | edit engine `comfyui` | Slashes trimmed on save; verify button; not required by the browser | `:1544`, `:3048`; `Images.svelte:814-860`; `images.py:303` |
| **API Key** (`Use an API key when your ComfyUI server requires one.`) | `images.edit.comfyui.api_key` | `IMAGES_EDIT_COMFYUI_API_KEY` | empty | edit engine `comfyui` | | `:1545`, `:3049`; `Images.svelte:862-872` |
| **ComfyUI Workflow** | `images.edit.comfyui.workflow` | `IMAGES_EDIT_COMFYUI_WORKFLOW` | empty (no default edit workflow) | edit engine `comfyui` | | `:1547`, `:3050`; `Images.svelte:874-943` |
| **ComfyUI Workflow Nodes** (`Map workflow node inputs used for image edits.`) | `images.edit.comfyui.nodes` | `IMAGES_EDIT_COMFYUI_WORKFLOW_NODES` | `[]` | edit engine `comfyui` and a workflow present | Five rows (5.3) | `:1549-1555`, `:3051`; `Images.svelte:945-994` |
| **Base URL** (Gemini) | `images.edit.gemini.api_base_url` | `IMAGES_EDIT_GEMINI_API_BASE_URL` | the value of `GEMINI_API_BASE_URL` | edit engine `gemini` | No built-in address | `:1540`, `:3046`; `Images.svelte:995-1005` |
| **API Key** (Gemini) | `images.edit.gemini.api_key` | `IMAGES_EDIT_GEMINI_API_KEY` | the value of `GEMINI_API_KEY` | edit engine `gemini` | The field is marked required while shown | `:1541`, `:3047`; `Images.svelte:1007-1016` |

(`Images.svelte` is `src/lib/components/admin/Settings/Images.svelte`; `images.py` is
`backend/open_webui/routers/images.py`.)

The fallbacks to `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `GEMINI_API_KEY` and
`GEMINI_API_BASE_URL` happen only when the settings are first seeded; afterwards changing the chat
connection does not change the image connection, unless one of the ground-truth exceptions
(`ENABLE_PERSISTENT_CONFIG=False`, `RESET_CONFIG_ON_START=True`) applies
(`backend/open_webui/config.py:1505-1541`; ground truth on persistent settings).

### 7.2 Checks When Saving

| Check | Where | Result | Source |
|---|---|---|---|
| Creation engine's required field (Automatic1111 or ComfyUI address, OpenAI-style or Gemini key) is empty | Browser | Pop-up, switch flipped off in the form, nothing saved (5.1) | `src/lib/components/admin/Settings/Images.svelte:110-134` |
| A workflow is not a JSON object | Browser | Pop-up, nothing saved | `src/lib/components/admin/Settings/Images.svelte:165-201` |
| **Image Size** is `auto` but **Model** does not match `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN` (default `^gpt-image`) | Server | 400, `Invalid format. Please use the correct format  (auto is only allowed with models matching ^gpt-image).` | `backend/open_webui/routers/images.py:278-286` |
| **Image Size** is not blank, `auto` or `{digits}x{digits}` | Server | 400, `Invalid format. Please use the correct format  (e.g., 512x512).` | `backend/open_webui/routers/images.py:288-293` |
| **Steps** below 0 | Server | 400, `Invalid format. Please use the correct format  (e.g., 50).` | `backend/open_webui/routers/images.py:295-299` |
| Edit **Image Size** | Not checked | Any text is saved; see 11.5 | `backend/open_webui/routers/images.py:276-304` |

The server messages are shown in the red pop-up by the panel
(`src/lib/components/admin/Settings/Images.svelte:147-150`).

### 7.3 Related Settings Elsewhere

| Setting | Where | Key | Default | Effect here | Source |
|---|---|---|---|---|---|
| `Image Prompt Generation Prompt` (`Rewrites user intent into an image-generation prompt.`, placeholder `Leave empty to use the default prompt, or enter a custom prompt`) | Admin Settings › Interface | `task.image.prompt_template` (`IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE`) | empty (built-in template) | Template for 5.7 | `src/lib/components/admin/Settings/Interface.svelte:537-546`; `backend/open_webui/config.py:2254`, `:3141`; `translation.json:2502-2503` |
| Task model | Admin Settings › Interface | see `chat-completion-pipeline-and-generation-tasks.md` | — | Writes the image prompt (5.7) | `backend/open_webui/routers/tasks.py:359` |
| `Image Generation` feature permission | Admin Panel › Users › Groups | `user.permissions` → `features.image_generation` (`USER_PERMISSIONS_FEATURES_IMAGE_GENERATION`) | on | Gate 3 of 3.2 | `backend/open_webui/config.py:1910-1912`, `:2010` |
| Model capabilities `Image Generation`, `Vision`; Builtin Tools `Image Generation`; Default Features `Image Generation`; **Function Calling** | Workspace › Models | model metadata | on when not set (capabilities and tool group); not ticked (default feature); native | Gates 4 to 7 of 3.2 | section 3.2 |
| Maximum upload size | Admin Settings › Documents | `rag.file.max_size` | see `files-uploads-and-storage.md` | Also limits generated pictures (5.10) | `backend/open_webui/routers/files.py:394-400` |
| Image compression width and height | Admin Settings › Documents | `file.image_compression_width`, `file.image_compression_height` | empty | Shrinks pictures attached in the composer (the sources of edits), not generated pictures | `backend/open_webui/config.py:989-995`; `src/lib/components/chat/MessageInput.svelte:1132-1166` |

### 7.4 Environment-Only Settings

| Variable | Default | Effect | Source |
|---|---|---|---|
| `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN` | `^gpt-image` | Which model names may use size `auto` | `backend/open_webui/config.py:1357-1358` |
| `IMAGE_URL_RESPONSE_MODELS_REGEX_PATTERN` | `^gpt-image` | For model names matching it, MedIT GPT does not ask an OpenAI-style service for inline (`b64_json`) results. The test uses the configured model name, not the per-request one | `backend/open_webui/config.py:1360-1361`; `backend/open_webui/routers/images.py:643-650`, `:992-999` |
| `ENABLE_OPENAI_IMAGE_EDIT_NORMALIZATION` | on | Rewrites awkward JPEG sources before OpenAI-style edits (4.1) | `backend/open_webui/config.py:1533` |
| `AIOHTTP_CLIENT_TIMEOUT` | unset (no overall limit; 300 seconds if the value cannot be read) | Time limit for every engine request (5.12) | `backend/open_webui/env.py:608-612`; `backend/open_webui/utils/session_pool.py:43-51` |
| `AIOHTTP_CLIENT_SESSION_SSL` | on | Certificate checking for engine connections; keep it on | `backend/open_webui/env.py:631` |
| `AIOHTTP_CLIENT_ALLOW_REDIRECTS` | off | Whether downloads of web-link source pictures for edits follow redirects | `backend/open_webui/env.py:637`; `backend/open_webui/routers/images.py:936-938` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` | off | When on, OpenAI-style image requests (create and edit) carry the user's name, id, email and role as headers, or as one signed token | `backend/open_webui/env.py:989-1007`; `backend/open_webui/routers/images.py:627-628`, `:983-984`; `backend/open_webui/utils/headers.py:38-60` |
| `AIOHTTP_POOL_CONNECTIONS`, `AIOHTTP_POOL_CONNECTIONS_PER_HOST` | unset, which means no limit (the module's opening notes say 100 and 30, but the code does not apply those numbers) | Connection limits of the shared pool used for engine requests | `backend/open_webui/env.py:710-726`; `backend/open_webui/utils/session_pool.py:8-11`, `:58-67` |

## 8. Cron Jobs and Background Processes

There is no scheduled job, background loop or Redis listener for images; image work happens inside
the request that asks for it. Search covered `backend/open_webui/routers/images.py`,
`backend/open_webui/utils/images/comfyui.py`, the image functions of
`backend/open_webui/utils/middleware.py` and `backend/open_webui/tools/builtin.py`, and the startup
list in `backend/open_webui/main.py:345-472` (`knowledgebase/tools/inventory.md` lists the seven
startup loops; none is about images).

| When | What happens | Source |
|---|---|---|
| Server start (module import) | The router creates `DATA_DIR/cache/image/generations/` if missing; nothing else uses it (6.4) | `backend/open_webui/routers/images.py:54-55` |
| Saving the Images tab | Settings are written at once; for Automatic1111 (or an empty engine) the server immediately asks the Automatic1111 server to load the chosen checkpoint, which affects everyone using that server. Failures are only logged at debug level | `backend/open_webui/routers/images.py:304-305`, `:172-199` |
| A chat message in legacy mode | The image step runs before the model is called, inside the chat request's own processing (`chat-completion-pipeline-and-generation-tasks.md` section 5.3) | `backend/open_webui/utils/middleware.py:2711-2720` |
| A native tool call | Runs in the tool loop of the reply | `backend/open_webui/tools/builtin.py:370-510` |
| A ComfyUI job | The server keeps a websocket open to ComfyUI and waits for the finished signal, then fetches the job history and pictures | `backend/open_webui/utils/images/comfyui.py:69-100`, `:189-214` |
| After a direct generation, edit or settings save | Event delivery (webhooks, event functions) is scheduled as separate asyncio tasks, so a slow webhook does not delay the picture | `backend/open_webui/events.py:1062-1066`, `:1159-1171`, `:1174-1201` |

## 9. Notifications and Emails

MedIT GPT sends no email (ground truth). Image work produces these browser and integration signals:

### 9.1 Websocket Events to the User's Page

| Event | Sent by | What the page does | Source |
|---|---|---|---|
| `status` with `Creating image` (saved chats only), `Image created`, `An error occurred while generating an image` | Legacy step | Adds a line to the reply's status list (hidden when the fork's **Hide Processing Details** is on, section 12) | `backend/open_webui/utils/middleware.py:1871-1876`, `:1890-1895`, `:1923-1931`, `:1998-2003`, `:2031-2039`; `src/lib/components/chat/Messages/ResponseMessage.svelte:197-199`, `:720-722` |
| `files` | Legacy step | Shows the pictures on the reply; the server also saves them into the message | `backend/open_webui/utils/middleware.py:1897-1910`, `:2005-2018`; `backend/open_webui/socket/main.py:1220-1233`; `src/lib/components/chat/Chat.svelte:1269-1270` |
| `chat:message:files` | `generate_image`, `edit_image` | Shows the pictures on the reply (the tool has already saved them) | `backend/open_webui/tools/builtin.py:414-423`, `:487-496`; `src/lib/components/chat/Chat.svelte:1269-1270` |
| `files` or `chat:message:files` in a channel | Either path | Adds the files to the channel and updates the channel message for its members | `backend/open_webui/socket/main.py:1103-1124` |

### 9.2 Integration Events (Webhooks and Event Functions)

| Event | When | Data | Source |
|---|---|---|---|
| `image.generated` (message `Image generated`) | After a successful `POST /api/v1/images/generations` (the playground or another API caller); **not** for chat paths | `model` (as sent by the caller; the playground sends none), `size`, `n`, `prompt_preview` (the first 300 characters of the prompt), plus the actor | `backend/open_webui/routers/images.py:579-593`; `backend/open_webui/events.py:636-638` |
| `image.edited` (message `Image edited`) | After a successful `POST /api/v1/images/edit`; not for chat paths | Same fields | `backend/open_webui/routers/images.py:879-893`; `backend/open_webui/events.py:639-641` |
| `config.updated` (subject `images`) | After an Images tab save | Whether creation and editing are on, and both engines | `backend/open_webui/routers/images.py:307-318`; `backend/open_webui/events.py:60-62` |

These go to admin-configured event webhooks that subscribe to them and to active Event functions
(`backend/open_webui/events.py:1034-1060`, `:1103-1171`); they are not in-app notifications
(`backend/open_webui/events.py:669-675`). The actor block holds the user's id, name, email and role
(`backend/open_webui/events.py:704`, `:974-985`), so **webhook payloads carry personal data and part
of the prompt**. Whether any webhook subscribes to these events in production is data: TO BE
CONFIRMED. Webhook set-up is documented in `notifications-webhooks-events-and-banners.md`.

## 10. Error, Warning and Notice Messages (Verbatim)

How server text reaches people: the admin panel and the playground print the server's `detail`
in a red pop-up (`src/lib/components/admin/Settings/Images.svelte:104-107`, `:147-150`, `:450-453`;
`src/lib/components/playground/Images.svelte:92-95`). In chat, legacy-mode failures show only the
status `An error occurred while generating an image`, and the model is given the `detail` text to
explain (`backend/open_webui/utils/middleware.py:1913-1933`, `:2021-2041`); native-mode failures are
returned to the model as `{"error": "{status}: {detail}"}`, the web framework's text form of the
error, for example `{"error": "400: Something went wrong :/"}`
(`backend/open_webui/tools/builtin.py:435-437`, `:508-510`; section 14). What the model then says
is not controlled by MedIT GPT.

The generic texts come from `_error_message` (`backend/open_webui/constants.py:16-23`):
`ERROR_MESSAGES.DEFAULT(text)` gives `[ERROR: {text}]`; given an exception object it gives
`[ERROR: {fallback}]` when a fallback is supplied and otherwise `Something went wrong :/`.

### 10.1 Admin Images Tab (Browser)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `AUTOMATIC1111 Base URL is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:111-118` | **Save** with engine Automatic1111 and an empty **Base URL**; the form's Image Generation switch is turned off and nothing is saved | Admin enters the address | None |
| `ComfyUI Base URL is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:119-123` | As above, engine ComfyUI | Admin enters the address | None |
| `OpenAI API Key is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:124-128` | As above, engine `Default (Open AI)` with an empty **API Key**; also blocks saving edit settings while Image Generation is off | Admin enters the key | Whether the key is meant to come from the environment (7.1) |
| `Gemini API Key is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:129-133` | As above, engine Gemini | Admin enters the key | None |
| `Invalid JSON format for ComfyUI Workflow.` | Error | `src/lib/components/admin/Settings/Images.svelte:179-184` | The creation workflow text is not a JSON object | Re-export from ComfyUI in API format | None |
| `Invalid JSON format for ComfyUI Edit Workflow.` | Error | `src/lib/components/admin/Settings/Images.svelte:196-201` | The edit workflow text is not a JSON object | As above | None |
| `Server connection verified` | Success | `src/lib/components/admin/Settings/Images.svelte:455-459`, `:526-530`, `:839-843`; `translation.json:2469` | The verify button reached the Automatic1111 or ComfyUI address | None | None |
| `*Prompt node ID(s) are required for image generation` | Notice | `src/lib/components/admin/Settings/Images.svelte:687-689`, `:990-992` | Always under the ComfyUI node rows (the form does not enforce it) | Map the prompt node | Node mapping (5.3) |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:891-896` | Save finished | None | None |
| `[object Object]` | Error | `src/lib/components/admin/Settings/Images.svelte:147-150` with `src/lib/apis/images/index.ts:53-58` | Derived from the code, not observed: the server rejected the form's shape (for example **Steps** that is not a whole number) and returned a list of field errors, which the panel prints as text | Correct the field | Ask which field was changed |

### 10.2 Images Router (Server)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Invalid format. Please use the correct format  (auto is only allowed with models matching {IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN}).` (with the default: `... matching ^gpt-image).`) | Error, HTTP 400 | `backend/open_webui/routers/images.py:278-286`; `backend/open_webui/constants.py:86` | Save with **Image Size** `auto` and a **Model** whose name does not match the pattern | Admin picks a fixed size or a matching model | `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN` |
| `Invalid format. Please use the correct format  (e.g., 512x512).` | Error, HTTP 400 | `backend/open_webui/routers/images.py:288-293` | **Image Size** is not blank, `auto` or `{digits}x{digits}` (for example `1024 x 1024` or `1024X1024`) | Admin types `1024x1024` | None |
| `Invalid format. Please use the correct format  (e.g., 50).` | Error, HTTP 400 | `backend/open_webui/routers/images.py:295-299` | **Steps** below 0 | Admin enters 0 or more | None |
| `Unsupported image engine` | Error, HTTP 400 | `backend/open_webui/routers/images.py:338-351` | The verify call named an engine other than Automatic1111 or ComfyUI (the panel never does) | None | API caller |
| `The URL you provided is invalid. Please double-check and try again.` | Error, HTTP 400 | `backend/open_webui/routers/images.py:353-359`; `backend/open_webui/constants.py:99` | The verify button could not reach the address, or the server answered with an error status (for example a wrong key) | Admin checks address and key | Engine reachability from the MedIT GPT server |
| `[ERROR: Failed to retrieve image generation models]` | Error, HTTP 400 | `backend/open_webui/routers/images.py:434-442` | The model list could not be read: ComfyUI or Automatic1111 unreachable, or the mapped model node does not match the workflow. Shown when the Images tab opens or is saved with Image Generation on | Admin checks the engine | Log `Failed to list image generation models: {e}` |
| `[ERROR: Failed to connect to the image generation engine]` | Error, HTTP 400 | `backend/open_webui/routers/images.py:202-225` | Automatic1111 (or an empty engine value): reading the server's current checkpoint failed. Happens on **every** creation request while the server is down, before any picture is attempted | Wait, or tell the admin | Log `Failed to get default model from automatic1111: {e}` |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error, HTTP 403 | `backend/open_webui/routers/images.py:565-577` (creation), `:865-877` (edit); `backend/open_webui/constants.py:70-72` | `POST /generations` with **Image Generation** off, or `POST /edit` with **Image Edit** off, or a non-admin without `features.image_generation`. Seen in the playground or by API callers | Ask an admin | Gates 1 to 3 (3.2) |
| `Something went wrong :/` | Error, HTTP 400 | `backend/open_webui/routers/images.py:841-845` (creation), `:1199-1204` (edit); `backend/open_webui/constants.py:16-23` | Any failure that is not an error status from the engine: engine unreachable or timed out, unexpected answer, ComfyUI job failed or a mapped node id is missing, a picture could not be downloaded or stored (including one larger than the upload limit), ComfyUI edit upload failed | Retry later; report | Server log around the time (10.7) |
| `[ERROR: {error}]`, for example `[ERROR: Bad Request]` or `[ERROR: Unauthorized]` | Error, HTTP 400 | `backend/open_webui/routers/images.py:841-845`, `:1199-1204` | An OpenAI-style or Gemini engine answered its main request with an error status; `{error}` is only the HTTP reason phrase, the engine's own explanation is not passed on (`:661`, `:713`, `:1040`, `:1097`). ComfyUI and Automatic1111 failures show `Something went wrong :/` instead: the ComfyUI helpers swallow errors and return nothing, and Automatic1111 creation does not check the status (`backend/open_webui/utils/images/comfyui.py:207-212`; `backend/open_webui/routers/images.py:819-830`) | Rephrase or retry; report repeated failures | Engine key, model name, size; the engine's own logs |
| `[ERROR: Error loading image]` | Error, HTTP 400 | `backend/open_webui/routers/images.py:969-975` | Edit: a source picture could not be read (bad inline data, a web link that failed or was refused, a storage error) | Attach the picture again | None |
| `We could not find what you're looking for :/` | Error, HTTP 404 | `backend/open_webui/routers/images.py:951`, `:969-970` via `backend/open_webui/routers/files.py:911-917`, `:953-957` | Edit: a source picture's file no longer exists or the user may not read it | Attach the picture again | File ownership (3.4) |
| `Failed to retrieve image data from the generation backend` | Internal (not shown) | `backend/open_webui/routers/images.py:520-522` | The engine's picture could not be obtained; becomes `Something went wrong :/` | — | Look for `Error loading image data` or `Url does not point to an image.` in the log |
| `Failed to upload images to ComfyUI.` | Internal (not shown) | `backend/open_webui/routers/images.py:1134-1136` | Edit with ComfyUI: uploading a source picture failed; becomes `Something went wrong :/` | — | Debug log `Error uploading images to ComfyUI: {e}` |

### 10.3 Chat (Legacy Step and Native Tools)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Creating image` | Status | `backend/open_webui/utils/middleware.py:1870-1876` | Legacy step starts, saved chats only | Wait | None |
| `Image created` | Status | `backend/open_webui/utils/middleware.py:1890-1895`, `:1998-2003` | The engine call returned without error. Also shown when the engine returned **no** pictures (for example a Gemini `generateContent` answer with text only, or a ComfyUI workflow without a `SaveImage` or `PreviewImage` node) | If no picture appears, report it | Engine answer; workflow nodes |
| `An error occurred while generating an image` | Status (error) | `backend/open_webui/utils/middleware.py:1923-1931`, `:2031-2039` | The legacy create or edit failed; the model is told the error text | Read the model's explanation; retry | 10.2 texts |
| `Image generation is disabled` | Status | `backend/open_webui/utils/middleware.py:1935-1944` | Meant for "requested while switched off", but the step already returns at `:1867` in that case, so in v0.11.4 it appears only if the switch changes between two reads a moment apart | — | `image_generation.enable` |
| `<context>The requested image has been edited and created and is now being shown to the user. Let them know that it has been generated.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1912` | Legacy edit succeeded | None | None |
| `<context>Image generation was attempted but failed. The system is currently unable to generate the image. Tell the user that the following error occurred: {error_message}</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1933` | Legacy edit failed; `{error_message}` is the server `detail` (empty for errors that are not HTTP errors) | None | 10.2 |
| `<context>Image generation was requested but the feature is currently disabled by the administrator, so no image was created. Let the user know that image generation is currently unavailable.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1946` | Same condition as `Image generation is disabled` | None | None |
| `<context>The requested image has been created by the system successfully and is now being shown to the user. Let the user know that the image they requested has been generated and is now shown in the chat.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:2020` | Legacy creation succeeded | None | None |
| `<context>Image generation was attempted but failed because of an error. The system is currently unable to generate the image. Tell the user that the following error occurred: {error_message}</context>` | Model-facing | `backend/open_webui/utils/middleware.py:2041` | Legacy creation failed | None | 10.2 |
| `Image prompt generation failed` | Internal (not shown) | `backend/open_webui/utils/middleware.py:1962-1969` | The image prompt task returned an error; the user's own words are used instead | — | Log traceback from `:1987` |
| `No JSON object found in the response` | Internal (not shown) | `backend/open_webui/utils/middleware.py:1977-1978` | Intended for a task answer without JSON; the user's words are used instead | — | None |
| `The image has been successfully generated and is already visible to the user in the chat. You do not need to display or embed the image again - just acknowledge that it has been created.` | Success (to the model) | `backend/open_webui/tools/builtin.py:425-432` | `generate_image` succeeded | None | None |
| `The edited image has been successfully generated and is already visible to the user in the chat. You do not need to display or embed the image again - just acknowledge that it has been created.` | Success (to the model) | `backend/open_webui/tools/builtin.py:498-505` | `edit_image` succeeded | None | None |
| `{"error": "Request context not available"}` | Error (to the model) | `backend/open_webui/tools/builtin.py:384-385`, `:457-458` | A tool was called without the server request (not expected from the chat page) | None | None |
| `{"error": "{e}"}` | Error (to the model) | `backend/open_webui/tools/builtin.py:435-437`, `:508-510` | The tool failed; `{e}` is the error, usually `{status}: {detail}` | Read the model's explanation | 10.2 |

### 10.4 Image Prompt Task (Server)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model '' was not found` | Error, HTTP 404 (API callers only) | `backend/open_webui/routers/tasks.py:354-358`; `backend/open_webui/constants.py:89` | The chat model named in the request is not in the model list; in the legacy step the failure is absorbed and the user's words are used | — | None |
| `An internal error has occurred.` | Error, HTTP 400 (not shown in chat) | `backend/open_webui/routers/tasks.py:394-400` | The task model call failed; in the legacy step the user's words are used | — | Log `Exception occurred` |

### 10.5 Playground

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a prompt` | Error | `src/lib/components/playground/Images.svelte:67-71` | **Run** (or Ctrl/Cmd+Enter) with an empty box | Type a description | None |
| `Running...` | Info | `src/lib/components/playground/Images.svelte:266-274` | Request in progress | Wait | 5.12 |
| `Generated images will appear here` | Notice | `src/lib/components/playground/Images.svelte:165-171` | No result yet on this visit | None | None |
| `{error}` (the server text) | Error | `src/lib/components/playground/Images.svelte:92-95` | Any 10.2 failure | As in 10.2 | As in 10.2 |
| `Failed to download image` | Error | `src/lib/components/playground/Images.svelte:100-113` | Clicking a result could not fetch it | Try again | None |

### 10.6 Composer, Chat Page, Permissions and API Client

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Selected model(s) do not support image inputs` | Error | `src/lib/components/chat/MessageInput.svelte:1126-1130` | Attaching a picture (for example to edit it) when no selected model has the **Vision** capability | Choose a vision-capable model | Model capabilities |
| `Model {{modelName}} is not vision capable` | Warning (red pop-up, the message is still sent) | `src/lib/components/chat/Chat.svelte:3336-3357` | Sending in a chat that contains pictures to a model without **Vision**, with the image toggle off | Turn the image toggle on to edit, or pick another model | Model capabilities |
| `This is a default user permission and will remain enabled.` | Notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:1071-1077` | Admin turns **Image Generation** off for a group while the default permission is on | Change the default permission instead | Ground truth on permissions |
| `Server connection failed` | Error | `src/lib/apis/images/index.ts:18-25`, `:53-60`, `:89-96`, `:121-128`, `:154-161`, `:186-193`, `:221-232`, `:273-284` | The server's reply was not a JSON error (server down, network failure, a proxy error page) | Retry; report | Server and proxy health |

### 10.7 Log Lines (Server Log, Not Shown to Users)

| Message | Level | Source | Meaning |
|---|---|---|---|
| `Failed to get default model from automatic1111: {e}` | Error with trace | `backend/open_webui/routers/images.py:221` | Automatic1111 options could not be read |
| `Failed to list image generation models: {e}` (the error text, or its type name when empty) | Error | `backend/open_webui/routers/images.py:435-438` | Model list failed |
| `Url does not point to an image.` | Error | `backend/open_webui/routers/images.py:504` | A returned link was not a picture |
| `Error loading image data: {e}` | Error with trace | `backend/open_webui/routers/images.py:516` | A picture could not be downloaded or decoded |
| `Setting image model to {model}` | Info | `backend/open_webui/routers/images.py:173` | Settings saved; model applied |
| `Image edit normalization skipped: {e}` | Debug | `backend/open_webui/routers/images.py:152` | A JPEG could not be normalized; sent as is |
| `Error uploading images to ComfyUI: {e}` | Debug | `backend/open_webui/routers/images.py:1135` | ComfyUI edit upload failed |
| `Error while queuing prompt: {e}` | Error with trace | `backend/open_webui/utils/images/comfyui.py:32` | ComfyUI refused the job (often a workflow or node problem) |
| `WebSocket closed unexpectedly: {msg.type}` | Error | `backend/open_webui/utils/images/comfyui.py:85` | ComfyUI dropped the connection mid-job |
| `Failed to connect to WebSocket server: {e}` | Error with trace | `backend/open_webui/utils/images/comfyui.py:208`, `:249` | Could not open the ComfyUI websocket |
| `Error during image generation: {e}` / `Error during image editing: {e}` | Error with trace | `backend/open_webui/utils/images/comfyui.py:211`, `:252` | Any other ComfyUI failure |
| `generate_image error: {e}` / `edit_image error: {e}` | Error with trace | `backend/open_webui/tools/builtin.py:436`, `:509` | A native tool call failed |
| `generating image prompt using model {task_model_id} for user {user.email} ` | Debug (contains the user's email) | `backend/open_webui/routers/tasks.py:361` | Image prompt task started |
| `Exception occurred` | Error with trace | `backend/open_webui/routers/tasks.py:396` | Image prompt task failed |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it can look at what the user sees and, if it has admin access, read the
Images tab, but it does not change settings, permissions or models. For every escalation send:
the time of the attempt with time zone, the chat link or id (`/c/{id}`), the model name shown in
the chat, the exact text on screen, whether the reply shows a tool entry (native mode) or status
lines such as `Creating image` (legacy mode), and whether the playground behaves the same (admins).
Do not send the prompt text or the pictures unless the user agrees; they may hold personal or
health information.

### 11.1 "The image button is missing"

**Symptom.** The Integrations menu has no **Image** row, or there is no Integrations button at all.

**Likely causes, in order.**
1. **Image Generation** is off on the Images tab (the code default) (3.2 gate 1).
2. The user lacks the `Image Generation` feature permission (gate 3), for example because the
   default permissions were changed.
3. One of the selected models lacks the **Image Generation** capability; with several models
   selected, all of them must have it (gate 4; `src/lib/components/chat/MessageInput.svelte:831-834`).
4. The page was open when the admin switched the feature on and has not been reloaded (5.1 step 7).
5. The user is `pending` (3.1).

**Diagnostic steps.** Ask which model or models are selected and whether a reload helps. Try
another model. With admin access, read the **Image Generation** switch and the user's groups'
**Features Permissions** (read only).

**Resolution.** Reload the page; choose a single model known to support images. If the feature is
switched off for everyone, explain that it is not available; whether MedIT GPT offers image
generation at all is a service decision (TO BE CONFIRMED).

**Escalation.** To the platform administrators: user's role and group names (no personal details
in tickets beyond what the service desk requires), model name, and that the toggle is missing.

### 11.2 "Image generation never finishes"

**Symptom.** `Creating image` stays in the reply's status list, the tool entry keeps spinning, or the
playground shows `Running...` for many minutes.

**Likely causes, in order.**
1. The engine is slow or has a queue (ComfyUI and Automatic1111 process one job after another;
   large sizes and many steps take longer). There is no time limit unless `AIOHTTP_CLIENT_TIMEOUT`
   is set (5.12).
2. ComfyUI never reported the job as finished; the server waits on ComfyUI's websocket until it
   does or the connection closes (`backend/open_webui/utils/images/comfyui.py:69-100`). Whether
   ComfyUI sends that signal after a failed job is ComfyUI behaviour (TO BE CONFIRMED).
3. The connection between the browser and MedIT GPT dropped; the picture may still arrive in the
   saved chat later (legacy: saved by the server, `backend/open_webui/socket/main.py:1220-1233`;
   native: saved by the tool, `backend/open_webui/tools/builtin.py:405-412`).
4. With the fork's **Hide Processing Details** on, the user sees `Thinking...` instead of the status
   lines, which can look like a hang (section 12).

**Diagnostic steps.** Ask how long they waited and whether reopening the chat later shows the
picture. Ask an admin whether the playground has the same delay with a short prompt.

**Resolution.** Ask the user to wait a few minutes and then reload the chat; suggest a simpler
request. If it is general, escalate.

**Escalation.** To the platform maintainer with the time window and chat id; they can check the
server log for `Error during image generation: {e}`, `WebSocket closed unexpectedly: {msg.type}`
or `Error while queuing prompt: {e}` (10.7) and the engine's own queue.

### 11.3 "It says the engine isn't configured"

**Symptom.** One of: the admin sees `OpenAI API Key is required.`, `Gemini API Key is required.`,
`ComfyUI Base URL is required.` or `AUTOMATIC1111 Base URL is required.` when saving; a user sees
`[ERROR: Failed to connect to the image generation engine]` (playground) or the model says image
generation is unavailable or failed.

**Likely causes, in order.**
1. The creation engine's key or address is empty; the browser refuses to save any change on the tab
   until it is filled, even edit settings (5.1 step 6.1).
2. Engine Automatic1111 (or an empty engine value) and the Automatic1111 server is unreachable;
   every creation request fails before trying (`backend/open_webui/routers/images.py:202-225`).
3. Gemini selected with an empty **Base URL**: the code has no built-in address, so requests fail
   with `Something went wrong :/` (7.1).
4. The edit engine's fields are filled but the creation engine's are not (or the reverse); they
   are separate (5.2).

**Diagnostic steps.** With admin access, read which engines are selected and whether their
address and key fields are filled (never copy a key into a ticket). For Automatic1111 or
ComfyUI, the admin can use the verify button (`Server connection verified` or
`The URL you provided is invalid. Please double-check and try again.`).

**Resolution.** Tier 1 explains that the feature needs administrator set-up and escalates.

**Escalation.** To the platform administrators: which engine, which message, time.

### 11.4 "My image came out the wrong size"

**Symptom.** The picture is square when a wide one was wanted, or smaller or larger than expected.

**Likely causes, in order.**
1. Size is set only by the administrator (**Image Size**, code default `512x512`); users and the
   model cannot choose a size on any MedIT GPT path (5.11).
2. The engine is Gemini, which receives no size at all (4.2).
3. **Image Size** is blank or `auto`: OpenAI-style services then choose; ComfyUI and Automatic1111
   use 512 x 512 (5.11).
4. For ComfyUI, the width and height rows are not mapped, so the workflow's own size is used (5.3).
5. The engine returned a different size; MedIT GPT does not check (5.11).
6. Edits use the separate edit **Image Size**, blank by default (7.1).

**Diagnostic steps.** Ask which path (chat or playground) and which size they got. With admin
access, read **Image Size** for create and edit and the engine.

**Resolution.** Explain that size is a site-wide setting. Asking the model for "a wide picture"
does not change the pixel size.

**Escalation.** Only if the site setting should change: to the platform administrators (a service
decision, TO BE CONFIRMED).

### 11.5 "Edit image doesn't work"

**Symptom.** Asking to change an attached picture produces a brand-new picture, an error, nothing,
or `Selected model(s) do not support image inputs`.

**Likely causes, in order.**
1. **Image Edit** is off (code default); then legacy mode creates a new picture instead and native
   mode offers no `edit_image` tool (3.2 gate 2).
2. **Image Generation** is off: the image toggle is hidden, and chat editing is reached only through
   it (3.2).
3. The image toggle was not turned on for the message (5.5 step 2).
4. The selected model has no **Vision** capability, so the picture cannot be attached
   (`Selected model(s) do not support image inputs`, 10.6).
5. Native mode: the model did not call `edit_image`, or passed a picture address the tool cannot
   read (`[ERROR: Error loading image]` or `We could not find what you're looking for :/`, 10.2).
6. The edit **Model** is blank (no fallback), the edit engine is set to a value the code does not
   handle, or the edit **Image Size** is malformed (for example `1024x`), which makes every edit
   fail before the engine is called (`backend/open_webui/routers/images.py:907-913`, `:977-1198`).
7. Engine refused the request (`[ERROR: {error}]`).

**Diagnostic steps.** Confirm the toggle was on and a picture was attached or generated earlier in
the same chat. Ask for the exact text. With admin access, read **Image Edit**, the edit engine,
edit **Model** and edit **Image Size**.

**Resolution.** Ask the user to turn on **Image**, attach the picture to the same message and
describe the change; choose a vision-capable model. Otherwise escalate.

**Escalation.** To the platform administrators with the chat id, model and message text.

### 11.6 "It said the image was created but no picture appears"

**Symptom.** `Image created` (legacy) or the model says the picture is ready, but nothing shows.

**Likely causes, in order.**
1. The engine answered without a picture: Gemini `generateContent` returned only text, or a ComfyUI
   workflow has no `SaveImage` or `PreviewImage` output node; the code treats an empty result as a
   success (`backend/open_webui/routers/images.py:723-737`; `backend/open_webui/utils/images/comfyui.py:89-100`).
2. Native mode: the model claims success without having called the tool (model behaviour).
3. The picture cannot be loaded by this viewer (shared chats, 3.4 and 11.14).

**Diagnostic steps.** Look for a tool entry in the reply (native) and whether it shows a result.
Reload the chat.

**Resolution.** Retry once; if it repeats for everyone, escalate.

**Escalation.** To the platform maintainer: engine type, chat id, time.

### 11.7 "I turned on Image but the model only answered in text"

**Symptom.** No tool entry, no status line, no picture; the model replies in words.

**Likely causes, in order.**
1. Native mode: the model decided not to call `generate_image`, or the model is poor at tool use
   (`builtin-native-tools.md`).
2. The model's **Builtin Tools › Image Generation** group or its **Builtin Tools** capability is off,
   so the tool is not offered although the toggle shows (3.2 gates 5 and 6).
3. **Image Generation** was switched off after the page loaded, so the toggle still shows until a
   reload: the tool is then not offered, and the legacy step stops silently when there is nothing
   to edit (`backend/open_webui/utils/tools.py:689-696`; `backend/open_webui/utils/middleware.py:1866-1868`).

**Diagnostic steps.** Try an explicit request ("Use the image tool to draw ..."). Try another model.

**Resolution.** Suggest an explicit request or a different model.

**Escalation.** To whoever manages the model (Workspace › Models) if a specific model never
generates: model name and chat id.

### 11.8 "It says 'Something went wrong :/' or '[ERROR: Bad Request]'"

**Symptom.** One of these texts in the playground, or the model reports it.

**Likely causes, in order.**
1. `[ERROR: {error}]`: an OpenAI-style or Gemini engine refused the request; common reasons are a
   wrong key or model name, an unsupported size for that model, or the provider rejecting the
   prompt. MedIT GPT shows only the status phrase (10.2). Which provider rules apply is outside the
   code (TO BE CONFIRMED).
2. `Something went wrong :/`: the engine was unreachable or timed out, the answer was unexpected,
   a ComfyUI job or node mapping failed, or the picture could not be stored (for example larger
   than the upload limit) (10.2).

**Diagnostic steps.** Note the exact text and time; ask whether a different, simpler request
works.

**Resolution.** Suggest rephrasing once; otherwise escalate.

**Escalation.** To the platform maintainer with the text and time so they can match the server log
(10.7) and the engine's logs.

### 11.9 "The picture doesn't match what I asked for"

**Symptom.** The picture is unrelated, generic, or ignores details.

**Likely causes, in order.**
1. Native mode: the chat model wrote its own prompt for the tool (5.4 step 5); it may have
   shortened or changed the request.
2. Legacy mode with **Image Prompt Generation** on: the task model rewrote the request from the last
   six messages (5.7).
3. ComfyUI without a mapped prompt node: the workflow's own placeholder text is drawn (5.3).
4. Legacy mode in a chat that already contains pictures with Image Edit on: the request became an
   edit of earlier pictures (5.6).

**Diagnostic steps.** Ask for the tool entry's input (native mode shows the prompt the model sent,
`builtin-native-tools.md` section 4.2). Ask whether it happens in a new chat.

**Resolution.** Suggest a more explicit description, or a new chat.

**Escalation.** If every ComfyUI picture ignores the prompt: to the platform administrators
(node mapping).

### 11.10 "Every new picture request edits my old picture"

**Symptom.** In a chat that already has a picture, asking for a new one changes the old one.

**Likely causes, in order.** Legacy mode with **Image Edit** on: the step edits the pictures in the
two most recent messages that have any (5.6).

**Diagnostic steps.** Check whether the reply shows status lines (legacy) rather than a tool entry.

**Resolution.** Start a new chat for an unrelated picture.

**Escalation.** None, unless the behaviour is unexpected for the site's chosen mode.

### 11.11 "I can't find the Playground" or "It sends me back to the start page"

**Symptom.** No **Playground** in the profile menu, or `/playground/images` returns to `/`.

**Likely causes, in order.** The playground is for admins only (3.1).

**Resolution.** Explain; use image generation in a chat instead.

**Escalation.** None.

### 11.12 "The playground says I don't have permission"

**Symptom.** `You do not have permission to access this resource. Please contact your administrator for assistance.`
in the playground.

**Likely causes, in order.** **Image Generation** (for creating) or **Image Edit** (for editing with
added pictures) is switched off; admins are not exempt from these switches (3.1).

**Resolution.** Remove the added pictures to create instead of edit, or ask an administrator to
turn the switch on.

**Escalation.** To the platform administrators if the switch should be on.

### 11.13 "Saving the Images settings does nothing" (Admin)

**Symptom.** After **Save** the spinner keeps turning and the button stays disabled; or a red
pop-up such as `[object Object]` or `Invalid format. Please use the correct format  (e.g., 512x512).`

**Likely causes, in order.**
1. An **Additional Parameters** box holds text that is not valid JSON. Both boxes are read when
   saving, whatever the engine, and a reading failure stops the save without a message and leaves
   the button disabled (`src/lib/components/admin/Settings/Images.svelte:136-146`, `:176-219`).
2. **Image Size** in a form other than `WIDTHxHEIGHT`, or `auto` with a non-GPT-Image model (7.2).
3. **Steps** not a whole number (`[object Object]`, 10.1).
4. An empty required engine field (11.3).

**Diagnostic steps.** Ask for the exact pop-up text, if any.

**Resolution.** Admin closes and reopens the Settings window (which resets the button), then
corrects the field. Tier 1 does not edit settings.

**Escalation.** To the platform maintainer if the form still will not save.

### 11.14 "Someone I shared the chat with can't see the picture"

**Symptom.** A shared copy of a chat shows a broken picture for the viewer.

**Likely causes, in order.**
1. The picture was made in native mode, which does not write the `chat_file` link that shared-chat
   access relies on (3.4). Whether this breaks the picture for viewers is TO BE CONFIRMED by
   testing.
2. The viewer has no access to the shared chat.

**Diagnostic steps.** Ask whether the owner sees the picture; whether the picture came from the
image toggle.

**Resolution.** The owner can download the picture and share it another way, if that is allowed for
the content.

**Escalation.** To the platform maintainer with the shared link and chat id, for testing.

### 11.15 "I see 'Thinking...' instead of 'Creating image'"

**Symptom.** While a picture is being made, the reply shows only `Thinking...`.

**Likely causes, in order.** The user's personal setting **Hide Processing Details** is on; it hides
status lines and tool entries but still shows the finished pictures (section 12).

**Resolution.** Explain; the user can turn the setting off under Settings › Interface to see
progress.

**Escalation.** None.

## 12. Local Customisations

**The image area itself matches upstream v0.11.4.** Read-only `git diff main...uoft` and
`git diff` (working tree) show no change in `backend/open_webui/routers/images.py`,
`backend/open_webui/utils/images/`, `backend/open_webui/utils/middleware.py`,
`backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/tools.py`,
`backend/open_webui/routers/tasks.py`, `backend/open_webui/config.py`,
`src/lib/components/admin/Settings/Images.svelte`, `src/routes/(app)/playground/`,
`src/lib/components/playground/`, `src/lib/apis/images/`,
`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` or
`src/lib/components/admin/Users/Groups/Permissions.svelte`. The fork's one change to
`src/lib/components/chat/MessageInput.svelte` (the task list) and the working-tree change to
`src/lib/components/chat/Chat.svelte` (resuming after a tool approval) do not touch images.

Fork changes that alter what users see here:

| Change | Effect on images | Source |
|---|---|---|
| Personal setting **Hide Processing Details** (`Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`) | Hides the legacy status lines (`Creating image`, `Image created`, `An error occurred while generating an image`) and the `generate_image` / `edit_image` tool entries; shows `Thinking...` while the reply is in progress. The finished pictures still appear. A failure is then visible only through the model's words | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-199`, `:214-221`, `:720-722`, `:920-921`; `src/lib/components/common/ToolCallDisplay.svelte:145`, `:196-200`; `src/lib/components/common/InterfaceSettings.svelte:1361-1369`; `translation.json:2923-2924` |
| Product name `MedIT GPT` | The playground's browser tab reads `Playground / MedIT GPT` with the default name | `backend/open_webui/env.py:951`; `src/routes/(app)/playground/+layout.svelte:15-17` |

The `ResponseMessage.svelte` and `ToolCallDisplay.svelte` behaviour above is the working tree of
2026-10-10, which refines the committed fork version (both hide status lines when the setting is
on). The full description of the setting is in `user-settings-and-personalisation.md` and
`builtin-native-tools.md` section 5.6.

## 13. Source File Index

| File | What it holds for this area | Key lines |
|---|---|---|
| `backend/open_webui/routers/images.py` | The images router: settings read and save, connection test, model list, creation and edit for all engines, picture download and storage, events | whole file (1,204 lines): keys `:67-102`; settings `:228-319`; verify `:338-359`; models `:362-442`; storage `:479-559`; create `:562-845`; edit `:848-1204` |
| `backend/open_webui/utils/images/comfyui.py` | ComfyUI client: queue, websocket wait, history, upload, node mapping | whole file (255 lines): `:17-100`, `:103-119`, `:147-186`, `:189-255` |
| `backend/open_webui/utils/middleware.py` | Legacy image step and its trigger | `:1733-1747`, `:1828-2046`, `:2711-2720` |
| `backend/open_webui/tools/builtin.py` | `generate_image` and `edit_image` native tools | `:365-510` |
| `backend/open_webui/utils/tools.py` | When the native image tools are offered | `:520-566`, `:687-704` |
| `backend/open_webui/routers/tasks.py` | Image prompt task | `:344-400` |
| `backend/open_webui/utils/task.py` | Fills the image prompt template | `:332-338` |
| `backend/open_webui/config.py` | Image settings, defaults, default ComfyUI workflow, permission default, prompt template | `:318-333`, `:1347-1555`, `:1910-1912`, `:2010`, `:2254-2274`, `:3019-3051`, `:3141` |
| `backend/open_webui/env.py` | Outbound request time limit, certificate and redirect settings, user-info headers | `:608-637`, `:710-726`, `:989-1007` |
| `backend/open_webui/utils/session_pool.py` | Shared outbound connection pool and time limit | `:43-79` |
| `backend/open_webui/constants.py` | Error texts used here | `:16-23`, `:70-72`, `:78`, `:86`, `:89`, `:99`, `:145` |
| `backend/open_webui/routers/files.py` | Upload path used for generated pictures; serving them | `:324-478`, `:795-855`, `:907-957` |
| `backend/open_webui/utils/access_control/files.py` | Who may read a picture file | `:19-102` |
| `backend/open_webui/models/chats.py` | `chat_file` table; saving pictures into the message; shared-chat lookup | `:217-243`, `:1274-1306`, `:2571-2664` |
| `backend/open_webui/models/files.py` | `file` table | `:18-31` |
| `backend/open_webui/socket/main.py` | Saving `files` events; channel file handling | `:1103-1124`, `:1220-1233` |
| `backend/open_webui/events.py` | `image.generated`, `image.edited`, `config.updated`; delivery | `:60-62`, `:636-641`, `:669-675`, `:704`, `:974-1060`, `:1103-1201` |
| `backend/open_webui/utils/automations.py` | Model default features for channels and automations | `:166-199` |
| `backend/open_webui/main.py` | Router mount; `enable_image_generation` sent to the browser | `:849`, `:2279`, `:2367` |
| `src/lib/components/admin/Settings/Images.svelte` | Admin Images tab | whole file (1,041 lines) |
| `src/lib/apis/images/index.ts` | Browser client for the images router | whole file (292 lines) |
| `src/lib/components/playground/Images.svelte` | Images playground | whole file (281 lines) |
| `src/routes/(app)/playground/+layout.svelte`, `src/routes/(app)/playground/images/+page.svelte` | Playground frame, tabs and Images page | whole files |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | Admin-only Playground menu entry | `:425-470` |
| `src/lib/components/chat/MessageInput.svelte` | Toggle visibility, image chip, Escape, image attach check | `:744-787`, `:831-834`, `:1126-1130`, `:2169-2177`, `:2295-2344`, `:2502-2519` |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | **Image** row in the Integrations menu | `:304-306`, `:471-494` |
| `src/lib/components/chat/Chat.svelte` | Default features, `?image-generation=true`, vision warning, `features` sent, `files` events | `:1083-1090`, `:1269-1270`, `:2176-2178`, `:3336-3357`, `:3393-3410` |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Pictures and status lines in the reply; Hide Processing Details | `:197-221`, `:720-746`, `:920-921` |
| `src/lib/components/chat/SettingsModal.svelte` | Images tab in the Settings window | `:172`, `:310-315`, `:891-896` |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | `Image Generation` feature permission | `:960`, `:1061-1078` |
| `src/lib/components/workspace/Models/Capabilities.svelte`, `BuiltinTools.svelte`, `DefaultFeatures.svelte` (same folder) | Model switches for images | `Capabilities.svelte:29-32`; `BuiltinTools.svelte:53-56`; `DefaultFeatures.svelte:17-20` |
| `src/lib/components/admin/Settings/Interface.svelte` | Image prompt template field | `:537-546` |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys used here | `:2415-2472`, `:2502-2503`, `:2552-2553`, `:2583-2584`, `:2594-2595`, `:2600-2601`, `:2923-2924` |

Files listed in the scope and read in full: `backend/open_webui/routers/images.py`,
`backend/open_webui/utils/images/comfyui.py`, `src/lib/components/admin/Settings/Images.svelte`,
`src/lib/apis/images/index.ts`, `src/lib/components/playground/Images.svelte`,
`src/routes/(app)/playground/+layout.svelte`, `src/routes/(app)/playground/+page.svelte`,
`src/routes/(app)/playground/images/+page.svelte`. A search of the other playground components
(`src/lib/components/playground/Chat.svelte`, `Completions.svelte` and the `Chat/` folder) finds no
mention of images; they are documented in `model-connections-openai-ollama-and-direct.md`.

## 14. Open Questions

### 14.1 Live Values and Deployment (TO BE CONFIRMED)

1. Whether production has **Image Generation** (`image_generation.enable`) and **Image Edit**
   (`images.edit.enable`) on; both are off in the code defaults. Data in the `config` table.
2. Which creation and edit engines, models, sizes and steps production uses, the engine
   addresses, and whether **Image Prompt Generation** is on. Data in the `config` table.
3. Which outside service production calls (an OpenAI-compatible provider, Google, or a
   self-hosted ComfyUI or Automatic1111), where it runs, and under which agreement. Not in the
   repository.
4. Whether the default or any group permission removes `features.image_generation` (data in
   `user.permissions` and groups).
5. Whether production models run in native or legacy **Function Calling** mode, and which have the
   **Image Generation** capability, builtin tool group or default feature (model data).
6. Environment values in production: `AIOHTTP_CLIENT_TIMEOUT`, `ENABLE_FORWARD_USER_INFO_HEADERS`,
   `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN`, `IMAGE_URL_RESPONSE_MODELS_REGEX_PATTERN`,
   `ENABLE_OPENAI_IMAGE_EDIT_NORMALIZATION`, `STORAGE_PROVIDER` (where pictures are stored).
7. Time limits imposed by any proxy or load balancer in front of MedIT GPT (section 5.12); the
   deployment is not described in the repository.
8. Whether any event webhook or Event function subscribes to `image.generated`, `image.edited` or
   `config.updated` (section 9.2), which would send user identity and the first 300 characters of
   prompts to that destination.
9. Whether `DATA_DIR/cache/image/generations/` holds pictures from older releases (section 6.4).
10. The address to enter for a Gemini **Base URL**: the code supplies none and the provider's
    address is not in the repository (section 7.1).

### 14.2 Behaviour That Needs a Test or Outside Knowledge

1. **Shared chats and native-mode pictures.** Native tools do not write a `chat_file` row, which
   the shared-chat read rule uses (section 3.4). Whether viewers of a shared copy can load such
   pictures needs a test.
2. **Which picture addresses models pass to `edit_image`.** The tool accepts several forms
   (section 5.5); what a given model actually passes is model behaviour.
3. **ComfyUI after a failed job.** The server waits for ComfyUI's "finished" signal on the
   websocket (section 5.12); whether ComfyUI sends it after an execution error is ComfyUI behaviour.
4. **Provider refusals.** Which HTTP status a provider uses for a refused prompt (and therefore which
   `[ERROR: {error}]` phrase users see) is provider behaviour, not in the code.
5. **`[object Object]` on save** (section 10.1) is derived from reading the code (a list of field
   errors printed as text); it was not observed.
6. **The `{status}: {detail}` text given to the model** on native tool failures relies on the web
   framework's error text format (Starlette 1.3.1 in the project virtual environment,
   `.venv/lib/python3.12/site-packages/starlette/exceptions.py:15`), outside the repository's own code.
7. Whether closing and reopening the Settings window is enough to clear a stuck **Save** button on
   the Images tab (section 11.13); inferred from the component being re-created, not observed.
8. **Gemini edits label every source picture as PNG** whatever its real type
   (`backend/open_webui/routers/images.py:1068-1088`); whether Gemini accepts a JPEG labelled this
   way needs a test.
9. **Automatic1111 checkpoint switching.** Saving the tab, or an admin's API request that names a
   model (the playground sends none), changes the checkpoint loaded on the shared Automatic1111 server for
   everyone (sections 5.11 and 8); whether production uses Automatic1111 at all is TO BE CONFIRMED.

### 14.3 Differences from the Brief and from Other Documents

1. **Storage location.** The research brief lists `DATA_DIR/cache/image/generations/` as the
   generated-image store. In v0.11.4 the router only creates that folder; pictures are stored
   through the storage provider as `generated-image` files (sections 6.1 and 6.4;
   `backend/open_webui/routers/images.py:54-55`, `:520-537`).
2. **`Image generation is disabled`.** `chat-completion-pipeline-and-generation-tasks.md` (its
   section 10 row for this status) describes it as shown when image generation is requested while
   switched off. The code returns earlier in that case (`backend/open_webui/utils/middleware.py:1866-1868`),
   so the status is effectively unreachable in v0.11.4 (section 10.3). Not a ground-truth
   contradiction; that document's owner may wish to check it.
3. No contradiction with `knowledgebase/tools/ground-truth.md` or `CLAUDE.md` was found.

### 14.4 Security-Sensitive Questions

1. How the server checks picture links returned by engines and source-picture links supplied for
   edits (sections 5.10 and 10.2), and the access rules of the `/cache/{path}` route that serves
   the cache folder (`backend/open_webui/main.py:3026-3051`). Security-sensitive: refer to the
   platform maintainer and U of T Information Security (security.utoronto.ca).
2. How engine keys are held and shown on the admin page is not documented here (rule 20); keys
   are cited by setting name only.

### 14.5 Privacy and Service Decisions

1. **Data sent outside MedIT GPT.** Prompts, and for edits the source pictures, go to the
   configured engine; with `ENABLE_FORWARD_USER_INFO_HEADERS` on, OpenAI-style requests also carry
   the user's name, id, email and role (section 7.4). ComfyUI keeps uploaded source pictures on its
   own server (`backend/open_webui/utils/images/comfyui.py:103-119`). Whether this is acceptable
   for MedIT GPT content, which may include health information, and which services are approved,
   is an organizational question: TO BE CONFIRMED with the platform's data steward and the
   U of T Privacy Office (privacy.utoronto.ca).
2. **Data kept inside MedIT GPT.** Every picture's file record stores the prompt, and for Gemini
   edits a full copy of the source pictures; S3 object tags, when enabled, hold the owner's email
   and name; webhook
   events carry identity and a prompt preview; a debug log line contains the user's email
   (sections 6.2, 9.2, 10.7). Retention and access rules for these are TO BE CONFIRMED.
3. **Whether image generation is offered at all**, to whom, and with which acceptable-use guidance,
   is a service decision that the code cannot show: TO BE CONFIRMED.
4. Support contacts and escalation routes for image problems: none exist in the repository
   (ground truth): TO BE CONFIRMED.
