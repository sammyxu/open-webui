# Repository Inventory (generated 2026-10-07 15:57 from /Users/sam/Sites/open-webui)

Enumerated from the working tree. This is the authoritative list of what exists. Verify an
individual path with `ls` before citing it in a document. Regenerate with
`python3 tools/inventory.py` after every release.

## Backend API routers (backend/open_webui/routers) — 31 items

Mounted under `/api/v1/<name>` except `ollama` (`/ollama`) and `openai` (`/openai`); see backend/open_webui/main.py.

- `analytics`
- `audio`
- `auths`
- `automations`
- `calendar`
- `channels`
- `chats`
- `configs`
- `evaluations`
- `files`
- `folders`
- `functions`
- `groups`
- `images`
- `knowledge`
- `memories`
- `models`
- `notes`
- `notifications`
- `ollama`
- `openai`
- `pipelines`
- `prompts`
- `retrieval`
- `scim`
- `skills`
- `tasks`
- `terminals`
- `tools`
- `users`
- `utils`

## Top-level endpoints defined in main.py (backend/open_webui/main.py) — 39 routes

- `/api/changelog`
- `/api/chat/actions/{action_id}`
- `/api/chat/completed`
- `/api/chat/completions`
- `/api/config`
- `/api/embeddings`
- `/api/events`
- `/api/events/webhooks`
- `/api/events/webhooks/{webhook_id}`
- `/api/message`
- `/api/message/count_tokens`
- `/api/models`
- `/api/models/base`
- `/api/models/unload`
- `/api/tasks`
- `/api/tasks/chat/{chat_id:path}`
- `/api/tasks/chat/{chat_id:path}/stop`
- `/api/tasks/stop/{task_id}`
- `/api/usage`
- `/api/v1/chat/completions`
- `/api/v1/chats/{id}/messages/{message_id}/resolve`
- `/api/v1/embeddings`
- `/api/v1/messages`
- `/api/v1/messages/count_tokens`
- `/api/v1/models`
- `/api/version`
- `/api/version/updates`
- `/cache/{path:path}`
- `/health`
- `/health/db`
- `/manifest.json`
- `/oauth/backchannel-logout`
- `/oauth/clients/{client_id}/authorize`
- `/oauth/clients/{client_id}/callback`
- `/oauth/{provider}/callback`
- `/oauth/{provider}/login`
- `/oauth/{provider}/login/callback`
- `/opensearch.xml`
- `/ready`

## Database tables (SQLAlchemy models) (backend/open_webui/models/*.py, backend/open_webui/internal/*.py) — 39 tables

- `access_grant`
- `api_key`
- `auth`
- `automation`
- `automation_run`
- `calendar`
- `calendar_event`
- `calendar_event_attendee`
- `channel`
- `channel_file`
- `channel_member`
- `channel_webhook`
- `chat`
- `chat_file`
- `chat_message`
- `config`
- `feedback`
- `file`
- `folder`
- `function`
- `group`
- `group_member`
- `knowledge`
- `knowledge_directory`
- `knowledge_file`
- `memory`
- `message`
- `message_reaction`
- `model`
- `note`
- `oauth_session`
- `pinned_note`
- `prompt`
- `prompt_history`
- `shared_chat`
- `skill`
- `tag`
- `tool`
- `user`

## Tables created by Alembic migrations (including the initial schema list) (backend/open_webui/migrations/versions/*.py) — 42 tables

`access_grant`, `api_key`, `auth`, `automation`, `automation_run`, `calendar`, `calendar_event`, `calendar_event_attendee`, `channel`, `channel_file`, `channel_member`, `channel_webhook`, `chat`, `chat_file`, `chat_message`, `chatidtag`, `config`, `document`, `feedback`, `file`, `folder`, `function`, `group`, `group_member`, `knowledge`, `knowledge_directory`, `knowledge_file`, `memory`, `message`, `message_reaction`, `model`, `note`, `oauth_session`, `pinned_note`, `prompt`, `prompt_history`, `prompt_new`, `shared_chat`, `skill`, `tag`, `tool`, `user`

## Background loops started at startup (backend/open_webui/**/*.py) — 7 loops

- `automation_worker_loop`
- `periodic_session_pool_cleanup`
- `periodic_usage_pool_cleanup`
- `redis_event_listener`
- `redis_task_command_listener`
- `redis_task_heartbeat`
- `scheduler_worker_loop`

## Enum members in constants.py (ERROR_MESSAGES, MESSAGES, WEBHOOK_MESSAGES, TASKS) (backend/open_webui/constants.py) — 70 constants

`ACCESS_PROHIBITED`, `ACTION_PROHIBITED`, `API_KEY_CREATION_NOT_ALLOWED`, `API_KEY_NOT_ALLOWED`, `API_KEY_NOT_FOUND`, `AUTOCOMPLETE_GENERATION`, `AUTOMATION_COUNT_REQUIRES_DTSTART`, `AUTOMATION_INVALID_RRULE`, `AUTOMATION_LIMIT_EXCEEDED`, `AUTOMATION_NO_FUTURE_RUNS`, `AUTOMATION_TOO_FREQUENT`, `CALENDAR_RRULE_TOO_FREQUENT`, `COMMAND_TAKEN`, `CREATE_API_KEY_ERROR`, `CREATE_USER_ERROR`, `DB_NOT_SQLITE`, `DEFAULT`, `DELETE_USER_ERROR`, `DUPLICATE_CONTENT`, `EMAIL_MISMATCH`, `EMAIL_TAKEN`, `EMOJI_GENERATION`, `EMPTY_CONTENT`, `ENV_VAR_NOT_FOUND`, `EXISTING_USERS`, `FEATURE_DISABLED`, `FILE_EXISTS`, `FILE_NOT_PROCESSED`, `FILE_NOT_SENT`, `FILE_NOT_SUPPORTED`, `FILE_TOO_LARGE`, `FOLLOW_UP_GENERATION`, `FUNCTION_CALLING`, `ID_TAKEN`, `IMAGE_PROMPT_GENERATION`, `INCORRECT_FORMAT`, `INCORRECT_PASSWORD`, `INPUT_TOO_LONG`, `INVALID_CRED`, `INVALID_EMAIL_FORMAT`, `INVALID_PASSWORD`, `INVALID_TOKEN`, `INVALID_TRUSTED_HEADER`, `INVALID_URL`, `MALICIOUS`, `MOA_RESPONSE_GENERATION`, `MODEL_ADDED`, `MODEL_DELETED`, `MODEL_ID_TAKEN`, `MODEL_ID_TOO_LONG`, `MODEL_NOT_FOUND`, `NAME_TAG_TAKEN`, `NOT_FOUND`, `OAUTH_NOT_CONFIGURED`, `OLLAMA_API_DISABLED`, `OLLAMA_NOT_FOUND`, `OPENAI_NOT_FOUND`, `PANDOC_NOT_INSTALLED`, `PASSWORD_TOO_LONG`, `QUERY_GENERATION`, `RATE_LIMIT_EXCEEDED`, `REQUIRED_FIELD_EMPTY`, `SERVER_CONNECTION_ERROR`, `TAGS_GENERATION`, `TITLE_GENERATION`, `UNAUTHORIZED`, `USERNAME_TAKEN`, `USER_NOT_FOUND`, `USER_SIGNUP`, `WEB_SEARCH_ERROR`

## Persistent config keys (DEFAULT_CONFIG) (backend/open_webui/config.py) — 405 keys

`audio.stt.allowed_extensions`, `audio.stt.azure.api_key`, `audio.stt.azure.base_url`, `audio.stt.azure.locales`, `audio.stt.azure.max_speakers`, `audio.stt.azure.region`, `audio.stt.deepgram.api_key`, `audio.stt.engine`, `audio.stt.mistral.api_base_url`, `audio.stt.mistral.api_key`, `audio.stt.mistral.use_chat_completions`, `audio.stt.model`, `audio.stt.openai.api_base_url`, `audio.stt.openai.api_key`, `audio.stt.openai.api_request_format`, `audio.stt.supported_content_types`, `audio.stt.whisper_model`, `audio.tts.api_key`, `audio.tts.azure.speech_base_url`, `audio.tts.azure.speech_output_format`, `audio.tts.azure.speech_region`, `audio.tts.engine`, `audio.tts.mistral.api_base_url`, `audio.tts.mistral.api_key`, `audio.tts.model`, `audio.tts.openai.api_base_url`, `audio.tts.openai.api_key`, `audio.tts.openai.params`, `audio.tts.split_on`, `audio.tts.voice`, `auth.admin.email`, `auth.admin.show`, `auth.api_key.allowed_endpoints`, `auth.api_key.endpoint_restrictions`, `auth.enable_api_keys`, `auth.jwt_expiry`, `automations.auth_token_expires_in`, `automations.enable`, `automations.max_count`, `automations.min_interval`, `calendar.enable`, `channels.enable`, `channels.model_response_mode`, `chat.context_compaction.enable`, `chat.context_compaction.model`, `chat.context_compaction.prompt_template`, `chat.context_compaction.retention_percentage`, `chat.context_compaction.token_cap`, `chat.context_compaction.token_threshold`, `chat.tool_permissions.enable`, `code_execution.enable`, `code_execution.engine`, `code_execution.jupyter.auth`, `code_execution.jupyter.auth_password`, `code_execution.jupyter.auth_token`, `code_execution.jupyter.timeout`, `code_execution.jupyter.url`, `code_interpreter.enable`, `code_interpreter.engine`, `code_interpreter.jupyter.auth`, `code_interpreter.jupyter.auth_password`, `code_interpreter.jupyter.auth_token`, `code_interpreter.jupyter.timeout`, `code_interpreter.jupyter.url`, `code_interpreter.prompt_template`, `direct.enable`, `direct.integrations.enable`, `evaluation.arena.enable`, `evaluation.arena.models`, `file.image_compression_height`, `file.image_compression_width`, `folders.enable`, `folders.max_file_count`, `google_drive.api_key`, `google_drive.client_id`, `google_drive.enable`, `image_generation.automatic1111.api_auth`, `image_generation.automatic1111.api_params`, `image_generation.automatic1111.base_url`, `image_generation.comfyui.api_key`, `image_generation.comfyui.base_url`, `image_generation.comfyui.nodes`, `image_generation.comfyui.workflow`, `image_generation.enable`, `image_generation.engine`, `image_generation.gemini.api_base_url`, `image_generation.gemini.api_key`, `image_generation.gemini.endpoint_method`, `image_generation.model`, `image_generation.openai.api_base_url`, `image_generation.openai.api_key`, `image_generation.openai.api_version`, `image_generation.openai.params`, `image_generation.prompt.enable`, `image_generation.size`, `image_generation.steps`, `images.edit.comfyui.api_key`, `images.edit.comfyui.base_url`, `images.edit.comfyui.nodes`, `images.edit.comfyui.workflow`, `images.edit.enable`, `images.edit.engine`, `images.edit.gemini.api_base_url`, `images.edit.gemini.api_key`, `images.edit.model`, `images.edit.openai.api_base_url`, `images.edit.openai.api_key`, `images.edit.openai.api_version`, `images.edit.size`, `ldap.enable`, `ldap.group.enable_creation`, `ldap.group.enable_management`, `ldap.server.app_dn`, `ldap.server.app_password`, `ldap.server.attribute_for_groups`, `ldap.server.attribute_for_mail`, `ldap.server.attribute_for_username`, `ldap.server.ca_cert_file`, `ldap.server.ciphers`, `ldap.server.host`, `ldap.server.label`, `ldap.server.port`, `ldap.server.search_filter`, `ldap.server.use_tls`, `ldap.server.users_dn`, `ldap.server.validate_cert`, `memories.background_review.enable`, `memories.context_char_limit`, `memories.enable`, `memories.review_interval_turns`, `memories.system_context.enable`, `memories.user_char_limit`, `models.base_models_cache`, `models.default_metadata`, `models.default_params`, `notes.enable`, `oauth.admin_roles`, `oauth.allowed_domains`, `oauth.allowed_roles`, `oauth.audience`, `oauth.auto_redirect`, `oauth.blocked_groups`, `oauth.client.timeout`, `oauth.client_id`, `oauth.client_secret`, `oauth.code_challenge_method`, `oauth.email_claim`, `oauth.enable`, `oauth.enable_group_creation`, `oauth.enable_group_mapping`, `oauth.enable_role_mapping`, `oauth.enable_signup`, `oauth.end_session_endpoint`, `oauth.feishu.client_id`, `oauth.feishu.client_secret`, `oauth.feishu.redirect_uri`, `oauth.feishu.scope`, `oauth.github.client_id`, `oauth.github.client_secret`, `oauth.github.redirect_uri`, `oauth.github.scope`, `oauth.google.client_id`, `oauth.google.client_secret`, `oauth.google.redirect_uri`, `oauth.google.scope`, `oauth.group_claim`, `oauth.group_default_share`, `oauth.merge_accounts_by_email`, `oauth.microsoft.client_id`, `oauth.microsoft.client_secret`, `oauth.microsoft.login_base_url`, `oauth.microsoft.picture_url`, `oauth.microsoft.redirect_uri`, `oauth.microsoft.scope`, `oauth.microsoft.tenant_id`, `oauth.picture_claim`, `oauth.provider_name`, `oauth.provider_url`, `oauth.redirect_uri`, `oauth.refresh_token.include_scope`, `oauth.roles_claim`, `oauth.scopes`, `oauth.sub_claim`, `oauth.timeout`, `oauth.token_endpoint_auth_method`, `oauth.update_email_on_login`, `oauth.update_name_on_login`, `oauth.update_picture_on_login`, `oauth.username_claim`, `ollama.api_configs`, `ollama.base_urls`, `ollama.enable`, `onedrive.enable`, `onedrive.sharepoint_tenant_id`, `onedrive.sharepoint_url`, `openai.api_base_urls`, `openai.api_configs`, `openai.api_keys`, `openai.enable`, `rag.azure_openai.api_key`, `rag.azure_openai.api_version`, `rag.azure_openai.base_url`, `rag.bypass_embedding_and_retrieval`, `rag.chunk_min_size_target`, `rag.chunk_overlap`, `rag.chunk_size`, `rag.content_extraction.supported_media_mime_types`, `rag.content_extraction_engine`, `rag.datalab_marker_additional_config`, `rag.datalab_marker_api_base_url`, `rag.datalab_marker_api_key`, `rag.datalab_marker_disable_image_extraction`, `rag.datalab_marker_force_ocr`, `rag.datalab_marker_format_lines`, `rag.datalab_marker_output_format`, `rag.datalab_marker_paginate`, `rag.datalab_marker_skip_cache`, `rag.datalab_marker_strip_existing_ocr`, `rag.datalab_marker_use_llm`, `rag.docling_api_key`, `rag.docling_params`, `rag.docling_server_url`, `rag.document_intelligence_endpoint`, `rag.document_intelligence_key`, `rag.document_intelligence_model`, `rag.embedding_batch_size`, `rag.embedding_concurrent_requests`, `rag.embedding_engine`, `rag.embedding_model`, `rag.enable_async_embedding`, `rag.enable_hybrid_search`, `rag.enable_hybrid_search_enriched_texts`, `rag.enable_markdown_header_text_splitter`, `rag.external_document_loader_api_key`, `rag.external_document_loader_headers`, `rag.external_document_loader_url`, `rag.external_reranker_api_key`, `rag.external_reranker_timeout`, `rag.external_reranker_url`, `rag.file.allowed_extensions`, `rag.file.max_count`, `rag.file.max_size`, `rag.full_context`, `rag.hybrid_bm25_weight`, `rag.mineru_api_key`, `rag.mineru_api_mode`, `rag.mineru_api_timeout`, `rag.mineru_api_url`, `rag.mineru_file_extensions`, `rag.mineru_params`, `rag.mistral_ocr_api_base_url`, `rag.mistral_ocr_api_key`, `rag.mistral_ocr_use_base64`, `rag.ollama.api_key`, `rag.ollama.base_url`, `rag.openai.api_base_url`, `rag.openai.api_key`, `rag.paddleocr_vl_base_url`, `rag.paddleocr_vl_token`, `rag.pdf_extract_images`, `rag.pdf_loader_mode`, `rag.relevance_threshold`, `rag.reranking_batch_size`, `rag.reranking_engine`, `rag.reranking_model`, `rag.template`, `rag.text_splitter`, `rag.tika_server_url`, `rag.tika_server_version`, `rag.tiktoken_encoding_name`, `rag.tokenizer_model`, `rag.top_k`, `rag.top_k_reranker`, `rag.youtube_loader_language`, `rag.youtube_loader_proxy_url`, `subagents.background_enabled`, `subagents.enable`, `subagents.max_async`, `subagents.max_concurrent`, `subagents.max_iterations`, `subagents.max_output`, `subagents.system_prompt`, `task.autocomplete.enable`, `task.autocomplete.input_max_length`, `task.autocomplete.prompt_template`, `task.follow_up.enable`, `task.follow_up.prompt_template`, `task.image.prompt_template`, `task.model.default`, `task.model.external`, `task.model.params`, `task.query.prompt_template`, `task.query.retrieval.enable`, `task.query.search.enable`, `task.tags.enable`, `task.tags.prompt_template`, `task.title.enable`, `task.title.prompt_template`, `task.tools.prompt_template`, `task.voice.prompt.enable`, `task.voice.prompt_template`, `terminal_server.connections`, `tool_server.connections`, `ui.banners`, `ui.default_group_id`, `ui.default_interface_settings`, `ui.default_locale`, `ui.default_models`, `ui.default_pinned_models`, `ui.default_user_role`, `ui.enable_community_sharing`, `ui.enable_login_form`, `ui.enable_message_rating`, `ui.enable_password_change_form`, `ui.enable_signup`, `ui.enable_user_webhooks`, `ui.i18n`, `ui.model_order_list`, `ui.pending_user_overlay_content`, `ui.pending_user_overlay_title`, `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n`, `ui.watermark`, `user.permissions`, `users.enable_status`, `web.fetch.max_content_length`, `web.loader.concurrent_requests`, `web.loader.engine`, `web.loader.external_web_loader_api_key`, `web.loader.external_web_loader_url`, `web.loader.firecrawl_api_key`, `web.loader.firecrawl_api_url`, `web.loader.firecrawl_timeout`, `web.loader.playwright_timeout`, `web.loader.playwright_ws_url`, `web.loader.ssl_verification`, `web.loader.timeout`, `web.search.azure_ai_search_api_key`, `web.search.azure_ai_search_endpoint`, `web.search.azure_ai_search_index_name`, `web.search.bing_search_v7_endpoint`, `web.search.bing_search_v7_subscription_key`, `web.search.bocha_search_api_key`, `web.search.brave_search_api_key`, `web.search.brave_search_context_tokens`, `web.search.bypass_embedding_and_retrieval`, `web.search.bypass_web_loader`, `web.search.concurrent_requests`, `web.search.confirmation.content`, `web.search.confirmation.enable`, `web.search.ddgs_backend`, `web.search.domain.filter_list`, `web.search.enable`, `web.search.engine`, `web.search.exa_api_key`, `web.search.exa_max_content_length`, `web.search.external_web_search_api_key`, `web.search.external_web_search_url`, `web.search.google_pse_api_key`, `web.search.google_pse_engine_id`, `web.search.jina_api_base_url`, `web.search.jina_api_key`, `web.search.kagi_search_api_key`, `web.search.linkup_api_key`, `web.search.linkup_search_params`, `web.search.microsoft_web_iq_api_base_url`, `web.search.microsoft_web_iq_api_key`, `web.search.microsoft_web_iq_language`, `web.search.mojeek_search_api_key`, `web.search.ollama_cloud_api_key`, `web.search.openserp_base_url`, `web.search.perplexity_api_key`, `web.search.perplexity_model`, `web.search.perplexity_search_api_url`, `web.search.perplexity_search_context_usage`, `web.search.result_count`, `web.search.searchapi_api_key`, `web.search.searchapi_engine`, `web.search.searxng_language`, `web.search.searxng_query_url`, `web.search.serpapi_api_key`, `web.search.serpapi_engine`, `web.search.serper_api_key`, `web.search.serphouse_api_key`, `web.search.serphouse_domain`, `web.search.serply_api_key`, `web.search.serpstack_api_key`, `web.search.serpstack_https`, `web.search.sougou_api_sid`, `web.search.sougou_api_sk`, `web.search.staan_api_key`, `web.search.staan_market`, `web.search.staan_max_snippets`, `web.search.tavily_api_key`, `web.search.tavily_extract_depth`, `web.search.trust_env`, `web.search.yacy_password`, `web.search.yacy_query_url`, `web.search.yacy_username`, `web.search.yandex_web_search_api_key`, `web.search.yandex_web_search_config`, `web.search.yandex_web_search_url`, `web.search.youcom_api_key`, `webhook_url`, `webui.url`

## Environment variables read in env.py and elsewhere (not config.py) (backend/open_webui/env.py, backend/open_webui/__init__.py, backend/open_webui/internal/*.py, backend/open_webui/utils/*.py, backend/open_webui/routers/*.py, backend/open_webui/retrieval/**/*.py, backend/open_webui/socket/*.py, backend/open_webui/storage/*.py) — 238 variables

`AIOHTTP_CLIENT_ALLOW_REDIRECTS`, `AIOHTTP_CLIENT_ASYNC_DNS_RESOLVER`, `AIOHTTP_CLIENT_SESSION_SSL`, `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL`, `AIOHTTP_CLIENT_SSL_CERT_FILE`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT`, `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST`, `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER`, `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA`, `AIOHTTP_FILE_STREAM_CHUNK_SIZE`, `AIOHTTP_POOL_CONNECTIONS`, `AIOHTTP_POOL_CONNECTIONS_PER_HOST`, `AIOHTTP_POOL_DNS_TTL`, `AUDIT_EXCLUDED_PATHS`, `AUDIT_INCLUDED_PATHS`, `AUDIT_LOGS_FILE_PATH`, `AUDIT_LOG_FILE_ROTATION_SIZE`, `AUDIT_LOG_LEVEL`, `AUDIT_UVICORN_LOGGER_NAMES`, `AUTOMATION_POLL_INTERVAL`, `AUXILIARY_EMBEDDING_MODEL`, `BING_SEARCH_V7_ENDPOINT`, `BING_SEARCH_V7_SUBSCRIPTION_KEY`, `BYPASS_MODEL_ACCESS_CONTROL`, `BYPASS_PYDUB_PREPROCESSING`, `BYPASS_RETRIEVAL_ACCESS_CONTROL`, `CALENDAR_ALERT_LOOKAHEAD_MINUTES`, `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES`, `CHAT_RESPONSE_STREAM_DELTA_CHUNK_SIZE`, `CHAT_STREAM_RESPONSE_CHUNK_MAX_BUFFER_SIZE`, `CUSTOM_API_KEY_HEADER`, `DATABASE_ENABLE_IAM_TOKEN_AUTH`, `DATABASE_ENABLE_SESSION_SHARING`, `DATABASE_ENABLE_SQLITE_WAL`, `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_PASSWORD`, `DATABASE_POOL_MAX_OVERFLOW`, `DATABASE_POOL_RECYCLE`, `DATABASE_POOL_SIZE`, `DATABASE_POOL_TIMEOUT`, `DATABASE_PORT`, `DATABASE_SCHEMA`, `DATABASE_SQLITE_PRAGMA_BUSY_TIMEOUT`, `DATABASE_SQLITE_PRAGMA_CACHE_SIZE`, `DATABASE_SQLITE_PRAGMA_JOURNAL_SIZE_LIMIT`, `DATABASE_SQLITE_PRAGMA_MMAP_SIZE`, `DATABASE_SQLITE_PRAGMA_SYNCHRONOUS`, `DATABASE_SQLITE_PRAGMA_TEMP_STORE`, `DATABASE_TYPE`, `DATABASE_URL`, `DATABASE_USER`, `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL`, `DATA_DIR`, `DEFAULT_GROUP_SHARE_PERMISSION`, `DEPLOYMENT_ID`, `DOCKER`, `ENABLE_ADMIN_CHAT_ACCESS`, `ENABLE_API_OUTLET_FILTERS`, `ENABLE_AUDIT_GET_REQUESTS`, `ENABLE_AUDIT_LOGS_FILE`, `ENABLE_AUDIT_STDOUT`, `ENABLE_CHAT_RESPONSE_BASE64_IMAGE_URL_CONVERSION`, `ENABLE_CHAT_RESPONSE_STREAM_INPLACE_APPEND`, `ENABLE_COMPRESSION_MIDDLEWARE`, `ENABLE_CUSTOM_MODEL_FALLBACK`, `ENABLE_DB_MIGRATIONS`, `ENABLE_EASTER_EGGS`, `ENABLE_FORWARD_USER_INFO_HEADERS`, `ENABLE_IMAGE_CONTENT_TYPE_EXTENSION_FALLBACK`, `ENABLE_INITIAL_ADMIN_SIGNUP`, `ENABLE_KB_EXEC`, `ENABLE_OAUTH_BACKCHANNEL_LOGOUT`, `ENABLE_OAUTH_EMAIL_FALLBACK`, `ENABLE_OAUTH_ID_TOKEN_COOKIE`, `ENABLE_OAUTH_TOKEN_EXCHANGE`, `ENABLE_OPENAI_API_PASSTHROUGH`, `ENABLE_ORJSON`, `ENABLE_OTEL`, `ENABLE_OTEL_LOGS`, `ENABLE_OTEL_METRICS`, `ENABLE_OTEL_TRACES`, `ENABLE_PASSWORD_VALIDATION`, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`, `ENABLE_PLUGINS`, `ENABLE_PROFILE_IMAGE_URL_FORWARDING`, `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`, `ENABLE_PYODIDE_FILE_PERSISTENCE`, `ENABLE_QUERIES_CACHE`, `ENABLE_RAG_CSV_SUMMARY`, `ENABLE_REALTIME_CHAT_SAVE`, `ENABLE_RESPONSES_API_STATEFUL`, `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS`, `ENABLE_SCIM`, `ENABLE_SIGNUP_PASSWORD_CONFIRMATION`, `ENABLE_STAR_SESSIONS_MIDDLEWARE`, `ENABLE_VALVE_ENCRYPTION`, `ENABLE_VERSION_UPDATE_CHECK`, `ENABLE_WEBSOCKET_SUPPORT`, `ENV`, `EXTERNAL_PWA_MANIFEST_URL`, `FORWARD_SESSION_INFO_HEADER_CHAT_ID`, `FORWARD_SESSION_INFO_HEADER_MESSAGE_ID`, `FORWARD_USER_INFO_HEADER_AUTH_TYPE`, `FORWARD_USER_INFO_HEADER_JWT`, `FORWARD_USER_INFO_HEADER_JWT_EXPIRES_SECONDS`, `FORWARD_USER_INFO_HEADER_JWT_SECRET`, `FORWARD_USER_INFO_HEADER_USER_EMAIL`, `FORWARD_USER_INFO_HEADER_USER_ID`, `FORWARD_USER_INFO_HEADER_USER_NAME`, `FORWARD_USER_INFO_HEADER_USER_ROLE`, `FROM_INIT_PY`, `FRONTEND_BUILD_DIR`, `GLOBAL_LOG_LEVEL`, `HF_HUB_CACHE`, `INSTANCE_ID`, `LD_LIBRARY_PATH`, `LICENSE_BLOB_PATH`, `LICENSE_KEY`, `LICENSE_PUBLIC_KEY`, `LOGURU_DIAGNOSE`, `LOG_FORMAT`, `MAX_BODY_LOG_SIZE`, `MCP_INITIALIZE_TIMEOUT`, `MINERU_MAX_MARKDOWN_BYTES`, `MODELS_CACHE_TTL`, `OAUTH_CLIENT_INFO_ENCRYPTION_KEY`, `OAUTH_MAX_SESSIONS_PER_USER`, `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY`, `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT`, `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT_WINDOW`, `OAUTH_TOKEN_EXCHANGE_TRUSTED_CLIENT_IDS`, `OFFLINE_MODE`, `OTEL_BASIC_AUTH_PASSWORD`, `OTEL_BASIC_AUTH_USERNAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_INSECURE`, `OTEL_LOGS_BASIC_AUTH_PASSWORD`, `OTEL_LOGS_BASIC_AUTH_USERNAME`, `OTEL_LOGS_EXPORTER_OTLP_ENDPOINT`, `OTEL_LOGS_EXPORTER_OTLP_INSECURE`, `OTEL_LOGS_OTLP_SPAN_EXPORTER`, `OTEL_METRICS_BASIC_AUTH_PASSWORD`, `OTEL_METRICS_BASIC_AUTH_USERNAME`, `OTEL_METRICS_EXPORTER_OTLP_ENDPOINT`, `OTEL_METRICS_EXPORTER_OTLP_INSECURE`, `OTEL_METRICS_EXPORT_INTERVAL_MILLIS`, `OTEL_METRICS_OTLP_SPAN_EXPORTER`, `OTEL_OTLP_SPAN_EXPORTER`, `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SERVICE_NAME`, `OTEL_TRACES_SAMPLER`, `PASSWORD_HASH_ALGORITHM`, `PASSWORD_VALIDATION_HINT`, `PASSWORD_VALIDATION_REGEX_PATTERN`, `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS`, `PROFILE_IMAGE_ALLOWED_MIME_TYPES`, `PROFILE_IMAGE_MAX_DATA_URI_SIZE`, `RAG_EMBEDDING_TIMEOUT`, `RAG_FILE_MAX_SIZE`, `RAG_METADATA_MAX_VALUE_CHARS`, `RAG_SOURCE_METADATA_KEYS`, `RAG_SYSTEM_CONTEXT`, `REDIS_CLUSTER`, `REDIS_HEALTH_CHECK_INTERVAL`, `REDIS_KEY_PREFIX`, `REDIS_RECONNECT_DELAY`, `REDIS_RESPONSE_STREAM_TTL`, `REDIS_SENTINEL_HOSTS`, `REDIS_SENTINEL_MAX_RETRY_COUNT`, `REDIS_SENTINEL_PORT`, `REDIS_SOCKET_CONNECT_TIMEOUT`, `REDIS_SOCKET_KEEPALIVE`, `REDIS_SOCKET_TIMEOUT`, `REDIS_TASK_TTL`, `REDIS_URL`, `REQUESTS_VERIFY`, `RESET_CONFIG_ON_START`, `SAFE_MODE`, `SCHEDULER_POLL_INTERVAL`, `SCIM_AUTH_PROVIDER`, `SCIM_ENABLED`, `SCIM_TOKEN`, `SEARXNG_CLIENT_CERT_FILE`, `SEARXNG_CLIENT_KEY_FILE`, `SENTENCE_TRANSFORMERS_BACKEND`, `SENTENCE_TRANSFORMERS_CROSS_ENCODER_BACKEND`, `SENTENCE_TRANSFORMERS_CROSS_ENCODER_MODEL_KWARGS`, `SENTENCE_TRANSFORMERS_CROSS_ENCODER_SIGMOID_ACTIVATION_FUNCTION`, `SENTENCE_TRANSFORMERS_HOME`, `SENTENCE_TRANSFORMERS_MODEL_KWARGS`, `STATIC_DIR`, `TAVILY_API_BASE_URL`, `TIMER_POLL_INTERVAL`, `TRUSTED_SIGNATURE_KEY`, `USER_AGENT`, `USE_CUDA_DOCKER`, `USE_SLIM_DOCKER`, `UVICORN_WORKERS`, `UVICORN_WS_PER_MESSAGE_DEFLATE`, `WEBSOCKET_EVENT_CALLER_TIMEOUT`, `WEBSOCKET_HEARTBEAT_INTERVAL`, `WEBSOCKET_MANAGER`, `WEBSOCKET_REDIS_CLUSTER`, `WEBSOCKET_REDIS_LOCK_TIMEOUT`, `WEBSOCKET_REDIS_OPTIONS`, `WEBSOCKET_REDIS_URL`, `WEBSOCKET_SENTINEL_HOSTS`, `WEBSOCKET_SENTINEL_PORT`, `WEBSOCKET_SERVER_ENGINEIO_LOGGING`, `WEBSOCKET_SERVER_LOGGING`, `WEBSOCKET_SERVER_PING_INTERVAL`, `WEBSOCKET_SERVER_PING_TIMEOUT`, `WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_NAME`, `WEBUI_ADMIN_PASSWORD`, `WEBUI_AUTH`, `WEBUI_AUTH_COOKIE_SAME_SITE`, `WEBUI_AUTH_COOKIE_SECURE`, `WEBUI_AUTH_SIGNOUT_REDIRECT_URL`, `WEBUI_AUTH_TRUSTED_EMAIL_HEADER`, `WEBUI_AUTH_TRUSTED_GROUPS_HEADER`, `WEBUI_AUTH_TRUSTED_NAME_HEADER`, `WEBUI_AUTH_TRUSTED_ROLE_HEADER`, `WEBUI_BUILD_HASH`, `WEBUI_JWT_SECRET_KEY`, `WEBUI_NAME`, `WEBUI_SECRET_KEY`, `WEBUI_SECRET_KEY_LENGTH`, `WEBUI_SESSION_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE`, `YANDEX_WEB_SEARCH_API_KEY`, `YANDEX_WEB_SEARCH_CONFIG`, `YANDEX_WEB_SEARCH_URL`

## Environment variables read in config.py (backend/open_webui/config.py) — 651 variables

`ADMIN_EMAIL`, `API_KEYS_ALLOWED_ENDPOINTS`, `API_KEY_ALLOWED_ENDPOINTS`, `AUDIO_STT_ALLOWED_EXTENSIONS`, `AUDIO_STT_AZURE_API_KEY`, `AUDIO_STT_AZURE_BASE_URL`, `AUDIO_STT_AZURE_LOCALES`, `AUDIO_STT_AZURE_MAX_SPEAKERS`, `AUDIO_STT_AZURE_REGION`, `AUDIO_STT_ENGINE`, `AUDIO_STT_MISTRAL_API_BASE_URL`, `AUDIO_STT_MISTRAL_API_KEY`, `AUDIO_STT_MISTRAL_USE_CHAT_COMPLETIONS`, `AUDIO_STT_MODEL`, `AUDIO_STT_OPENAI_API_BASE_URL`, `AUDIO_STT_OPENAI_API_KEY`, `AUDIO_STT_OPENAI_API_REQUEST_FORMAT`, `AUDIO_STT_SUPPORTED_CONTENT_TYPES`, `AUDIO_TTS_API_KEY`, `AUDIO_TTS_AZURE_SPEECH_BASE_URL`, `AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT`, `AUDIO_TTS_AZURE_SPEECH_REGION`, `AUDIO_TTS_ENGINE`, `AUDIO_TTS_MISTRAL_API_BASE_URL`, `AUDIO_TTS_MISTRAL_API_KEY`, `AUDIO_TTS_MODEL`, `AUDIO_TTS_OPENAI_API_BASE_URL`, `AUDIO_TTS_OPENAI_API_KEY`, `AUDIO_TTS_OPENAI_PARAMS`, `AUDIO_TTS_SPLIT_ON`, `AUDIO_TTS_VOICE`, `AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH`, `AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE`, `AUTOMATIC1111_API_AUTH`, `AUTOMATIC1111_BASE_URL`, `AUTOMATIC1111_PARAMS`, `AUTOMATION_AUTH_TOKEN_EXPIRES_IN`, `AUTOMATION_MAX_COUNT`, `AUTOMATION_MIN_INTERVAL`, `AZURE_AI_SEARCH_API_KEY`, `AZURE_AI_SEARCH_ENDPOINT`, `AZURE_AI_SEARCH_INDEX_NAME`, `AZURE_STORAGE_CONTAINER_NAME`, `AZURE_STORAGE_ENDPOINT`, `AZURE_STORAGE_KEY`, `BING_SEARCH_V7_ENDPOINT`, `BING_SEARCH_V7_SUBSCRIPTION_KEY`, `BOCHA_SEARCH_API_KEY`, `BRAVE_SEARCH_API_KEY`, `BRAVE_SEARCH_CONTEXT_TOKENS`, `BYPASS_ADMIN_ACCESS_CONTROL`, `BYPASS_EMBEDDING_AND_RETRIEVAL`, `BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL`, `BYPASS_WEB_SEARCH_WEB_LOADER`, `CHANNEL_MODEL_RESPONSE_MODE`, `CHROMA_CLIENT_AUTH_CREDENTIALS`, `CHROMA_CLIENT_AUTH_PROVIDER`, `CHROMA_DATABASE`, `CHROMA_HTTP_HEADERS`, `CHROMA_HTTP_HOST`, `CHROMA_HTTP_PORT`, `CHROMA_HTTP_SSL`, `CHROMA_TENANT`, `CHUNK_MIN_SIZE_TARGET`, `CHUNK_OVERLAP`, `CHUNK_SIZE`, `CODE_EXECUTION_ENGINE`, `CODE_EXECUTION_JUPYTER_AUTH`, `CODE_EXECUTION_JUPYTER_AUTH_PASSWORD`, `CODE_EXECUTION_JUPYTER_AUTH_TOKEN`, `CODE_EXECUTION_JUPYTER_TIMEOUT`, `CODE_EXECUTION_JUPYTER_URL`, `CODE_INTERPRETER_BLOCKED_MODULES`, `CODE_INTERPRETER_ENGINE`, `CODE_INTERPRETER_JUPYTER_AUTH`, `CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD`, `CODE_INTERPRETER_JUPYTER_AUTH_TOKEN`, `CODE_INTERPRETER_JUPYTER_TIMEOUT`, `CODE_INTERPRETER_JUPYTER_URL`, `CODE_INTERPRETER_PROMPT_TEMPLATE`, `COMFYUI_API_KEY`, `COMFYUI_BASE_URL`, `COMFYUI_WORKFLOW`, `COMFYUI_WORKFLOW_NODES`, `CONTENT_EXTRACTION_ENGINE`, `CONTENT_EXTRACTION_SUPPORTED_MEDIA_MIME_TYPES`, `CONTEXT_COMPACTION_MODEL`, `CONTEXT_COMPACTION_PROMPT_TEMPLATE`, `CONTEXT_COMPACTION_RETENTION_PERCENTAGE`, `CONTEXT_COMPACTION_TOKEN_CAP`, `CONTEXT_COMPACTION_TOKEN_THRESHOLD`, `CORS_ALLOW_CUSTOM_SCHEME`, `CORS_ALLOW_ORIGIN`, `CUSTOM_NAME`, `DATALAB_MARKER_ADDITIONAL_CONFIG`, `DATALAB_MARKER_API_BASE_URL`, `DATALAB_MARKER_API_KEY`, `DATALAB_MARKER_DISABLE_IMAGE_EXTRACTION`, `DATALAB_MARKER_FORCE_OCR`, `DATALAB_MARKER_FORMAT_LINES`, `DATALAB_MARKER_OUTPUT_FORMAT`, `DATALAB_MARKER_PAGINATE`, `DATALAB_MARKER_SKIP_CACHE`, `DATALAB_MARKER_STRIP_EXISTING_OCR`, `DATALAB_MARKER_USE_LLM`, `DDGS_BACKEND`, `DEEPGRAM_API_KEY`, `DEFAULT_GROUP_ID`, `DEFAULT_INTERFACE_SETTINGS`, `DEFAULT_LOCALE`, `DEFAULT_MODELS`, `DEFAULT_MODEL_METADATA`, `DEFAULT_MODEL_PARAMS`, `DEFAULT_PINNED_MODELS`, `DEFAULT_PROMPT_SUGGESTIONS`, `DEFAULT_USER_ROLE`, `DOCLING_API_KEY`, `DOCLING_PARAMS`, `DOCLING_SERVER_URL`, `DOCUMENT_INTELLIGENCE_ENDPOINT`, `DOCUMENT_INTELLIGENCE_KEY`, `DOCUMENT_INTELLIGENCE_MODEL`, `ELASTICSEARCH_API_KEY`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_CLOUD_ID`, `ELASTICSEARCH_INDEX_PREFIX`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, `ELEVENLABS_API_BASE_URL`, `ENABLE_ADMIN_ANALYTICS`, `ENABLE_ADMIN_EXPORT`, `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`, `ENABLE_API_KEYS`, `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS`, `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS`, `ENABLE_ASYNC_EMBEDDING`, `ENABLE_AUTOCOMPLETE_GENERATION`, `ENABLE_AUTOMATIONS`, `ENABLE_BASE_MODELS_CACHE`, `ENABLE_CALENDAR`, `ENABLE_CHANNELS`, `ENABLE_CODE_EXECUTION`, `ENABLE_CODE_INTERPRETER`, `ENABLE_COMMUNITY_SHARING`, `ENABLE_CONTEXT_COMPACTION`, `ENABLE_DIRECT_CONNECTIONS`, `ENABLE_DIRECT_INTEGRATIONS`, `ENABLE_EVALUATION_ARENA_MODELS`, `ENABLE_FOLDERS`, `ENABLE_FOLLOW_UP_GENERATION`, `ENABLE_GOOGLE_DRIVE_INTEGRATION`, `ENABLE_IMAGE_EDIT`, `ENABLE_IMAGE_GENERATION`, `ENABLE_IMAGE_PROMPT_GENERATION`, `ENABLE_KNOWLEDGE_FILE_RETENTION`, `ENABLE_LDAP`, `ENABLE_LDAP_GROUP_CREATION`, `ENABLE_LDAP_GROUP_MANAGEMENT`, `ENABLE_LOCAL_WEB_FETCH`, `ENABLE_LOGIN_FORM`, `ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER`, `ENABLE_MEMORIES`, `ENABLE_MEMORY_BACKGROUND_REVIEW`, `ENABLE_MEMORY_SYSTEM_CONTEXT`, `ENABLE_MESSAGE_RATING`, `ENABLE_MILVUS_MULTITENANCY_MODE`, `ENABLE_NOTES`, `ENABLE_OAUTH`, `ENABLE_OAUTH_GROUP_CREATION`, `ENABLE_OAUTH_GROUP_MANAGEMENT`, `ENABLE_OAUTH_PERSISTENT_CONFIG`, `ENABLE_OAUTH_ROLE_MANAGEMENT`, `ENABLE_OAUTH_SIGNUP`, `ENABLE_OLLAMA_API`, `ENABLE_ONEDRIVE_BUSINESS`, `ENABLE_ONEDRIVE_INTEGRATION`, `ENABLE_ONEDRIVE_PERSONAL`, `ENABLE_OPENAI_API`, `ENABLE_OPENAI_IMAGE_EDIT_NORMALIZATION`, `ENABLE_PASSWORD_AUTH`, `ENABLE_PASSWORD_CHANGE_FORM`, `ENABLE_PERSISTENT_CONFIG`, `ENABLE_QDRANT_MULTITENANCY_MODE`, `ENABLE_RAG_HYBRID_SEARCH`, `ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS`, `ENABLE_RAG_LOCAL_WEB_FETCH`, `ENABLE_RETRIEVAL_QUERY_GENERATION`, `ENABLE_SEARCH_QUERY_GENERATION`, `ENABLE_SIGNUP`, `ENABLE_SUBAGENTS`, `ENABLE_TAGS_GENERATION`, `ENABLE_TITLE_GENERATION`, `ENABLE_TOOL_PERMISSIONS`, `ENABLE_USER_STATUS`, `ENABLE_USER_WEBHOOKS`, `ENABLE_VOICE_MODE_PROMPT`, `ENABLE_WEB_LOADER_SSL_VERIFICATION`, `ENABLE_WEB_SEARCH`, `ENABLE_WEB_SEARCH_CONFIRMATION`, `EVALUATION_ARENA_MODELS`, `EXA_API_KEY`, `EXA_MAX_CONTENT_LENGTH`, `EXTERNAL_DOCUMENT_LOADER_API_KEY`, `EXTERNAL_DOCUMENT_LOADER_HEADERS`, `EXTERNAL_DOCUMENT_LOADER_URL`, `EXTERNAL_WEB_LOADER_API_KEY`, `EXTERNAL_WEB_LOADER_URL`, `EXTERNAL_WEB_SEARCH_API_KEY`, `EXTERNAL_WEB_SEARCH_URL`, `FEISHU_CLIENT_ID`, `FEISHU_CLIENT_SECRET`, `FEISHU_OAUTH_SCOPE`, `FEISHU_REDIRECT_URI`, `FILE_IMAGE_COMPRESSION_HEIGHT`, `FILE_IMAGE_COMPRESSION_WIDTH`, `FIRECRAWL_API_BASE_URL`, `FIRECRAWL_API_KEY`, `FIRECRAWL_TIMEOUT`, `FOLDER_MAX_FILE_COUNT`, `FOLLOW_UP_GENERATION_PROMPT_TEMPLATE`, `GCS_BUCKET_NAME`, `GEMINI_API_BASE_URL`, `GEMINI_API_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_REDIRECT_URI`, `GITHUB_CLIENT_SCOPE`, `GITHUB_CLIENT_SECRET`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_DRIVE_API_KEY`, `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_OAUTH_AUTHORIZE_PARAMS`, `GOOGLE_OAUTH_SCOPE`, `GOOGLE_PSE_API_KEY`, `GOOGLE_PSE_ENGINE_ID`, `GOOGLE_REDIRECT_URI`, `IFRAME_CSP`, `IMAGES_EDIT_COMFYUI_API_KEY`, `IMAGES_EDIT_COMFYUI_BASE_URL`, `IMAGES_EDIT_COMFYUI_WORKFLOW`, `IMAGES_EDIT_COMFYUI_WORKFLOW_NODES`, `IMAGES_EDIT_GEMINI_API_BASE_URL`, `IMAGES_EDIT_GEMINI_API_KEY`, `IMAGES_EDIT_OPENAI_API_BASE_URL`, `IMAGES_EDIT_OPENAI_API_KEY`, `IMAGES_EDIT_OPENAI_API_VERSION`, `IMAGES_GEMINI_API_BASE_URL`, `IMAGES_GEMINI_API_KEY`, `IMAGES_GEMINI_ENDPOINT_METHOD`, `IMAGES_OPENAI_API_BASE_URL`, `IMAGES_OPENAI_API_KEY`, `IMAGES_OPENAI_API_VERSION`, `IMAGES_OPENAI_PARAMS`, `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN`, `IMAGE_EDIT_ENGINE`, `IMAGE_EDIT_MODEL`, `IMAGE_EDIT_SIZE`, `IMAGE_GENERATION_ENGINE`, `IMAGE_GENERATION_MODEL`, `IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE`, `IMAGE_SIZE`, `IMAGE_STEPS`, `IMAGE_URL_RESPONSE_MODELS_REGEX_PATTERN`, `JINA_API_BASE_URL`, `JINA_API_KEY`, `JWT_EXPIRES_IN`, `K8S_FLAG`, `KAGI_SEARCH_API_KEY`, `LDAP_APP_DN`, `LDAP_APP_PASSWORD`, `LDAP_ATTRIBUTE_FOR_GROUPS`, `LDAP_ATTRIBUTE_FOR_MAIL`, `LDAP_ATTRIBUTE_FOR_USERNAME`, `LDAP_CA_CERT_FILE`, `LDAP_CIPHERS`, `LDAP_SEARCH_BASE`, `LDAP_SEARCH_FILTER`, `LDAP_SEARCH_FILTERS`, `LDAP_SERVER_HOST`, `LDAP_SERVER_LABEL`, `LDAP_SERVER_PORT`, `LDAP_USE_TLS`, `LDAP_VALIDATE_CERT`, `LINKUP_API_KEY`, `LINKUP_SEARCH_PARAMS`, `MARIADB_VECTOR_DB_URL`, `MARIADB_VECTOR_DISTANCE_STRATEGY`, `MARIADB_VECTOR_INDEX_M`, `MARIADB_VECTOR_INITIALIZE_MAX_VECTOR_LENGTH`, `MARIADB_VECTOR_POOL_MAX_OVERFLOW`, `MARIADB_VECTOR_POOL_RECYCLE`, `MARIADB_VECTOR_POOL_SIZE`, `MARIADB_VECTOR_POOL_TIMEOUT`, `MEMORIES_CONTEXT_CHAR_LIMIT`, `MEMORIES_REVIEW_INTERVAL_TURNS`, `MEMORIES_USER_CHAR_LIMIT`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_LOGIN_BASE_URL`, `MICROSOFT_CLIENT_PICTURE_URL`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_CLIENT_TENANT_ID`, `MICROSOFT_OAUTH_SCOPE`, `MICROSOFT_REDIRECT_URI`, `MICROSOFT_WEB_IQ_API_BASE_URL`, `MICROSOFT_WEB_IQ_API_KEY`, `MICROSOFT_WEB_IQ_LANGUAGE`, `MILVUS_COLLECTION_PREFIX`, `MILVUS_DB`, `MILVUS_DISKANN_MAX_DEGREE`, `MILVUS_DISKANN_SEARCH_LIST_SIZE`, `MILVUS_HNSW_EFCONSTRUCTION`, `MILVUS_HNSW_M`, `MILVUS_INDEX_TYPE`, `MILVUS_IVF_FLAT_NLIST`, `MILVUS_METRIC_TYPE`, `MILVUS_TOKEN`, `MILVUS_URI`, `MINERU_API_KEY`, `MINERU_API_MODE`, `MINERU_API_TIMEOUT`, `MINERU_API_URL`, `MINERU_FILE_EXTENSIONS`, `MINERU_PARAMS`, `MISTRAL_OCR_API_BASE_URL`, `MISTRAL_OCR_API_KEY`, `MISTRAL_OCR_USE_BASE64`, `MODEL_ORDER_LIST`, `MOJEEK_SEARCH_API_KEY`, `OAUTH_ACCESS_TOKEN_REQUEST_INCLUDE_CLIENT_ID`, `OAUTH_ADMIN_ROLES`, `OAUTH_ALLOWED_DOMAINS`, `OAUTH_ALLOWED_ROLES`, `OAUTH_AUDIENCE`, `OAUTH_AUTHORIZE_PARAMS`, `OAUTH_AUTO_REDIRECT`, `OAUTH_BLOCKED_GROUPS`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_CLIENT_TIMEOUT`, `OAUTH_CODE_CHALLENGE_METHOD`, `OAUTH_EMAIL_CLAIM`, `OAUTH_GROUPS_CLAIM`, `OAUTH_GROUPS_SEPARATOR`, `OAUTH_GROUP_CLAIM`, `OAUTH_GROUP_DEFAULT_SHARE`, `OAUTH_MERGE_ACCOUNTS_BY_EMAIL`, `OAUTH_PICTURE_CLAIM`, `OAUTH_PROVIDER_NAME`, `OAUTH_REFRESH_TOKEN_INCLUDE_SCOPE`, `OAUTH_ROLES_CLAIM`, `OAUTH_ROLES_SEPARATOR`, `OAUTH_SCOPES`, `OAUTH_SUB_CLAIM`, `OAUTH_TIMEOUT`, `OAUTH_TOKEN_ENDPOINT_AUTH_METHOD`, `OAUTH_UPDATE_EMAIL_ON_LOGIN`, `OAUTH_UPDATE_NAME_ON_LOGIN`, `OAUTH_UPDATE_PICTURE_ON_LOGIN`, `OAUTH_USERNAME_CLAIM`, `OLLAMA_API_BASE_URL`, `OLLAMA_API_CONFIGS`, `OLLAMA_BASE_URL`, `OLLAMA_BASE_URLS`, `OLLAMA_CLOUD_API_KEY`, `ONEDRIVE_CLIENT_ID`, `ONEDRIVE_CLIENT_ID_BUSINESS`, `ONEDRIVE_CLIENT_ID_PERSONAL`, `ONEDRIVE_SHAREPOINT_TENANT_ID`, `ONEDRIVE_SHAREPOINT_URL`, `OPENAI_API_BASE_URL`, `OPENAI_API_BASE_URLS`, `OPENAI_API_CONFIGS`, `OPENAI_API_KEY`, `OPENAI_API_KEYS`, `OPENGAUSS_DB_URL`, `OPENGAUSS_INITIALIZE_MAX_VECTOR_LENGTH`, `OPENGAUSS_POOL_MAX_OVERFLOW`, `OPENGAUSS_POOL_RECYCLE`, `OPENGAUSS_POOL_SIZE`, `OPENGAUSS_POOL_TIMEOUT`, `OPENID_END_SESSION_ENDPOINT`, `OPENID_PROVIDER_URL`, `OPENID_REDIRECT_URI`, `OPENSEARCH_CERT_VERIFY`, `OPENSEARCH_PASSWORD`, `OPENSEARCH_SSL`, `OPENSEARCH_URI`, `OPENSEARCH_USERNAME`, `OPENSERP_BASE_URL`, `ORACLE_DB_DSN`, `ORACLE_DB_PASSWORD`, `ORACLE_DB_POOL_INCREMENT`, `ORACLE_DB_POOL_MAX`, `ORACLE_DB_POOL_MIN`, `ORACLE_DB_USER`, `ORACLE_DB_USE_WALLET`, `ORACLE_VECTOR_LENGTH`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD`, `PADDLEOCR_VL_BASE_URL`, `PADDLEOCR_VL_TOKEN`, `PDF_EXTRACT_IMAGES`, `PDF_LOADER_MODE`, `PENDING_USER_OVERLAY_CONTENT`, `PENDING_USER_OVERLAY_TITLE`, `PERPLEXITY_API_KEY`, `PERPLEXITY_MODEL`, `PERPLEXITY_SEARCH_API_URL`, `PERPLEXITY_SEARCH_CONTEXT_USAGE`, `PGVECTOR_CREATE_EXTENSION`, `PGVECTOR_DB_URL`, `PGVECTOR_HNSW_EF_CONSTRUCTION`, `PGVECTOR_HNSW_M`, `PGVECTOR_INDEX_METHOD`, `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH`, `PGVECTOR_ITERATIVE_SCAN`, `PGVECTOR_IVFFLAT_LISTS`, `PGVECTOR_PGCRYPTO`, `PGVECTOR_PGCRYPTO_KEY`, `PGVECTOR_POOL_MAX_OVERFLOW`, `PGVECTOR_POOL_RECYCLE`, `PGVECTOR_POOL_SIZE`, `PGVECTOR_POOL_TIMEOUT`, `PGVECTOR_USE_HALFVEC`, `PINECONE_API_KEY`, `PINECONE_CLOUD`, `PINECONE_DIMENSION`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`, `PINECONE_METRIC`, `PLAYWRIGHT_TIMEOUT`, `PLAYWRIGHT_WS_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_PREFIX`, `QDRANT_GRPC_PORT`, `QDRANT_HNSW_M`, `QDRANT_ON_DISK`, `QDRANT_PREFER_GRPC`, `QDRANT_TIMEOUT`, `QDRANT_URI`, `QUERY_GENERATION_PROMPT_TEMPLATE`, `RAG_ALLOWED_FILE_EXTENSIONS`, `RAG_AZURE_OPENAI_API_KEY`, `RAG_AZURE_OPENAI_API_VERSION`, `RAG_AZURE_OPENAI_BASE_URL`, `RAG_EMBEDDING_BATCH_SIZE`, `RAG_EMBEDDING_CONCURRENT_REQUESTS`, `RAG_EMBEDDING_CONTENT_PREFIX`, `RAG_EMBEDDING_ENGINE`, `RAG_EMBEDDING_MODEL`, `RAG_EMBEDDING_MODEL_AUTO_UPDATE`, `RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE`, `RAG_EMBEDDING_OPENAI_BATCH_SIZE`, `RAG_EMBEDDING_PREFIX_FIELD_NAME`, `RAG_EMBEDDING_QUERY_PREFIX`, `RAG_EXTERNAL_RERANKER_API_KEY`, `RAG_EXTERNAL_RERANKER_TIMEOUT`, `RAG_EXTERNAL_RERANKER_URL`, `RAG_FILE_CONTENT_SEARCH_MAX_CHARS`, `RAG_FILE_MAX_COUNT`, `RAG_FILE_MAX_SIZE`, `RAG_FULL_CONTEXT`, `RAG_HYBRID_BM25_WEIGHT`, `RAG_OLLAMA_API_KEY`, `RAG_OLLAMA_BASE_URL`, `RAG_OPENAI_API_BASE_URL`, `RAG_OPENAI_API_KEY`, `RAG_RELEVANCE_THRESHOLD`, `RAG_RERANKING_BATCH_SIZE`, `RAG_RERANKING_ENGINE`, `RAG_RERANKING_MODEL`, `RAG_RERANKING_MODEL_AUTO_UPDATE`, `RAG_RERANKING_MODEL_TRUST_REMOTE_CODE`, `RAG_TEMPLATE`, `RAG_TEXT_SPLITTER`, `RAG_TOKENIZER_MODEL`, `RAG_TOP_K`, `RAG_TOP_K_RERANKER`, `RESPONSE_WATERMARK`, `S3_ACCESS_KEY_ID`, `S3_ADDRESSING_STYLE`, `S3_BUCKET_NAME`, `S3_ENABLE_TAGGING`, `S3_ENDPOINT_URL`, `S3_KEY_PREFIX`, `S3_REGION_NAME`, `S3_SECRET_ACCESS_KEY`, `S3_USE_ACCELERATE_ENDPOINT`, `S3_VECTOR_BUCKET_NAME`, `S3_VECTOR_REGION`, `SEARCHAPI_API_KEY`, `SEARCHAPI_ENGINE`, `SEARXNG_LANGUAGE`, `SEARXNG_QUERY_URL`, `SERPAPI_API_KEY`, `SERPAPI_ENGINE`, `SERPER_API_KEY`, `SERPHOUSE_API_KEY`, `SERPHOUSE_DOMAIN`, `SERPLY_API_KEY`, `SERPSTACK_API_KEY`, `SERPSTACK_HTTPS`, `SHOW_ADMIN_DETAILS`, `SOUGOU_API_SID`, `SOUGOU_API_SK`, `SSL_ASSERT_FINGERPRINT`, `STAAN_API_KEY`, `STAAN_MARKET`, `STAAN_MAX_SNIPPETS`, `STATIC_DIR`, `STORAGE_LOCAL_CACHE`, `STORAGE_PROVIDER`, `SUBAGENTS_BACKGROUND_ENABLED`, `SUBAGENTS_MAX_ASYNC`, `SUBAGENTS_MAX_CONCURRENT`, `SUBAGENTS_MAX_ITERATIONS`, `SUBAGENTS_MAX_OUTPUT`, `SUBAGENTS_SYSTEM_PROMPT`, `TAGS_GENERATION_PROMPT_TEMPLATE`, `TASK_MODEL`, `TASK_MODEL_EXTERNAL`, `TASK_MODEL_PARAMS`, `TAVILY_API_KEY`, `TAVILY_EXTRACT_DEPTH`, `TERMINAL_PROXY_HEADERS`, `TERMINAL_SERVER_CONNECTIONS`, `THREAD_POOL_SIZE`, `THREAD_POOL_THREAD_NAME_PREFIX`, `TIKA_SERVER_URL`, `TIKA_SERVER_VERSION`, `TIKTOKEN_CACHE_DIR`, `TIKTOKEN_ENCODING_NAME`, `TITLE_GENERATION_PROMPT_TEMPLATE`, `TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE`, `TOOL_SERVER_CONNECTIONS`, `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_GROUPS`, `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS`, `USER_PERMISSIONS_CALENDAR_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_CHAT_ALLOW_OPEN_SHARING`, `USER_PERMISSIONS_CHAT_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_CHAT_CALL`, `USER_PERMISSIONS_CHAT_CONTINUE_RESPONSE`, `USER_PERMISSIONS_CHAT_CONTROLS`, `USER_PERMISSIONS_CHAT_DELETE`, `USER_PERMISSIONS_CHAT_DELETE_MESSAGE`, `USER_PERMISSIONS_CHAT_EDIT`, `USER_PERMISSIONS_CHAT_EXPORT`, `USER_PERMISSIONS_CHAT_FILE_UPLOAD`, `USER_PERMISSIONS_CHAT_IMPORT`, `USER_PERMISSIONS_CHAT_MULTIPLE_MODELS`, `USER_PERMISSIONS_CHAT_PARAMS`, `USER_PERMISSIONS_CHAT_RATE_RESPONSE`, `USER_PERMISSIONS_CHAT_REGENERATE_RESPONSE`, `USER_PERMISSIONS_CHAT_SHARE`, `USER_PERMISSIONS_CHAT_STT`, `USER_PERMISSIONS_CHAT_SYSTEM_PROMPT`, `USER_PERMISSIONS_CHAT_TEMPORARY`, `USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED`, `USER_PERMISSIONS_CHAT_TTS`, `USER_PERMISSIONS_CHAT_VALVES`, `USER_PERMISSIONS_CHAT_WEB_UPLOAD`, `USER_PERMISSIONS_FEATURES_API_KEYS`, `USER_PERMISSIONS_FEATURES_AUTOMATIONS`, `USER_PERMISSIONS_FEATURES_CALENDAR`, `USER_PERMISSIONS_FEATURES_CHANNELS`, `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER`, `USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS`, `USER_PERMISSIONS_FEATURES_FOLDERS`, `USER_PERMISSIONS_FEATURES_IMAGE_GENERATION`, `USER_PERMISSIONS_FEATURES_MEMORIES`, `USER_PERMISSIONS_FEATURES_NOTES`, `USER_PERMISSIONS_FEATURES_USER_WEBHOOKS`, `USER_PERMISSIONS_FEATURES_WEB_SEARCH`, `USER_PERMISSIONS_FOLDERS_ALLOW_SHARING`, `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_NOTES_ALLOW_SHARING`, `USER_PERMISSIONS_SETTINGS_INTERFACE`, `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS`, `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS`, `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_MODELS_EXPORT`, `USER_PERMISSIONS_WORKSPACE_MODELS_IMPORT`, `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS`, `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_PROMPTS_EXPORT`, `USER_PERMISSIONS_WORKSPACE_PROMPTS_IMPORT`, `USER_PERMISSIONS_WORKSPACE_SKILLS_ACCESS`, `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_SKILLS_EXPORT`, `USER_PERMISSIONS_WORKSPACE_SKILLS_IMPORT`, `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS`, `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING`, `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_TOOLS_EXPORT`, `USER_PERMISSIONS_WORKSPACE_TOOLS_IMPORT`, `USE_OLLAMA_DOCKER`, `VALKEY_COLLECTION_PREFIX`, `VALKEY_DISTANCE_METRIC`, `VALKEY_HNSW_EF_CONSTRUCTION`, `VALKEY_HNSW_EF_RUNTIME`, `VALKEY_HNSW_M`, `VALKEY_INDEX_TYPE`, `VALKEY_URL`, `VECTOR_DB`, `VOICE_MODE_PROMPT_TEMPLATE`, `WEAVIATE_API_KEY`, `WEAVIATE_GRPC_HOST`, `WEAVIATE_GRPC_PORT`, `WEAVIATE_GRPC_SECURE`, `WEAVIATE_HTTP_HOST`, `WEAVIATE_HTTP_PORT`, `WEAVIATE_HTTP_SECURE`, `WEAVIATE_SKIP_INIT_CHECKS`, `WEBHOOK_URL`, `WEBUI_BANNERS`, `WEBUI_URL`, `WEB_FETCH_FILTER_LIST`, `WEB_FETCH_MAX_CONTENT_LENGTH`, `WEB_LOADER_CONCURRENT_REQUESTS`, `WEB_LOADER_ENGINE`, `WEB_LOADER_TIMEOUT`, `WEB_SEARCH_CONCURRENT_REQUESTS`, `WEB_SEARCH_CONFIRMATION_CONTENT`, `WEB_SEARCH_DOMAIN_FILTER_LIST`, `WEB_SEARCH_ENGINE`, `WEB_SEARCH_RESULT_COUNT`, `WEB_SEARCH_TRUST_ENV`, `WHISPER_COMPUTE_TYPE`, `WHISPER_LANGUAGE`, `WHISPER_MODEL`, `WHISPER_MODEL_AUTO_UPDATE`, `WHISPER_MODEL_DIR`, `WHISPER_MULTILINGUAL`, `WHISPER_VAD_FILTER`, `YACY_PASSWORD`, `YACY_QUERY_URL`, `YACY_USERNAME`, `YANDEX_WEB_SEARCH_API_KEY`, `YANDEX_WEB_SEARCH_CONFIG`, `YANDEX_WEB_SEARCH_URL`, `YDC_API_KEY`, `YOUCOM_API_KEY`, `YOUTUBE_LOADER_LANGUAGE`, `YOUTUBE_LOADER_PROXY_URL`

## Built-in (native) tools (backend/open_webui/tools/builtin.py) — 53 functions

`add_memory`, `ask_user`, `calculate_timestamp`, `create_automation`, `create_calendar_event`, `create_tasks`, `delegate_task`, `delete_automation`, `delete_calendar_event`, `delete_memory`, `edit_image`, `execute_code`, `fetch_url`, `generate_image`, `get_current_timestamp`, `grep_chat_files`, `grep_knowledge_files`, `list_automations`, `list_chat_files`, `list_knowledge`, `list_knowledge_bases`, `list_memories`, `list_memory_paths`, `notify`, `query_chat_files`, `query_knowledge_bases`, `query_knowledge_files`, `read_memory_path`, `replace_memory_content`, `replace_note_content`, `search_calendar_events`, `search_channel_messages`, `search_channels`, `search_chats`, `search_knowledge_bases`, `search_knowledge_files`, `search_memories`, `search_notes`, `search_web`, `timer`, `toggle_automation`, `update_automation`, `update_calendar_event`, `update_memory`, `update_task`, `view_channel_message`, `view_channel_thread`, `view_chat`, `view_file`, `view_knowledge_file`, `view_note`, `view_skill`, `write_note`

## Socket.IO event handlers (backend/open_webui/socket/*.py) — 13 events

- `*`
- `events:channel`
- `events:chat`
- `heartbeat`
- `join-channels`
- `join-note`
- `usage`
- `user-join`
- `ydoc:awareness:update`
- `ydoc:document:join`
- `ydoc:document:leave`
- `ydoc:document:state`
- `ydoc:document:update`

## Web search providers (backend/open_webui/retrieval/web) — 32 items

- `azure`
- `bing`
- `bocha`
- `brave`
- `brave_llm_context`
- `duckduckgo`
- `exa`
- `external`
- `firecrawl`
- `google_pse`
- `jina_search`
- `kagi`
- `linkup`
- `microsoft_web_iq`
- `mojeek`
- `ollama`
- `openserp`
- `perplexity`
- `perplexity_search`
- `searchapi`
- `searxng`
- `serpapi`
- `serper`
- `serphouse`
- `serply`
- `serpstack`
- `sougou`
- `staan`
- `tavily`
- `yacy`
- `yandex`
- `ydc`

## Vector database backends (backend/open_webui/retrieval/vector/dbs) — 15 items

- `chroma`
- `elasticsearch`
- `mariadb_vector`
- `milvus`
- `milvus_multitenancy`
- `opengauss`
- `opensearch`
- `oracle23ai`
- `pgvector`
- `pinecone`
- `qdrant`
- `qdrant_multitenancy`
- `s3vector`
- `valkey`
- `weaviate`

## Content extraction loaders (backend/open_webui/retrieval/loaders) — 12 items

- `datalab_marker`
- `external_document`
- `external_web`
- `local`
- `main`
- `microsoft_web_iq`
- `mineru`
- `mistral`
- `paddleocr_vl`
- `pdf`
- `tavily`
- `youtube`

## Frontend pages (SvelteKit routes) (src/routes) — 47 pages

`(app)/+page.svelte`, `(app)/admin/+page.svelte`, `(app)/admin/analytics/+page.svelte`, `(app)/admin/analytics/[tab]/+page.svelte`, `(app)/admin/evaluations/+page.svelte`, `(app)/admin/evaluations/[tab]/+page.svelte`, `(app)/admin/functions/+page.svelte`, `(app)/admin/functions/create/+page.svelte`, `(app)/admin/functions/edit/+page.svelte`, `(app)/admin/settings/+page.svelte`, `(app)/admin/settings/[tab]/+page.svelte`, `(app)/admin/users/+page.svelte`, `(app)/admin/users/[tab]/+page.svelte`, `(app)/automations/+page.svelte`, `(app)/automations/[id]/+page.svelte`, `(app)/c/[id]/+page.svelte`, `(app)/calendar/+page.svelte`, `(app)/channels/[id]/+page.svelte`, `(app)/folders/[folderId]/+page.svelte`, `(app)/home/+page.svelte`, `(app)/notes/+page.svelte`, `(app)/notes/[id]/+page.svelte`, `(app)/notes/new/+page.svelte`, `(app)/playground/+page.svelte`, `(app)/playground/completions/+page.svelte`, `(app)/playground/images/+page.svelte`, `(app)/workspace/+page.svelte`, `(app)/workspace/functions/create/+page.svelte`, `(app)/workspace/knowledge/+page.svelte`, `(app)/workspace/knowledge/[id]/+page.svelte`, `(app)/workspace/knowledge/create/+page.svelte`, `(app)/workspace/models/+page.svelte`, `(app)/workspace/models/create/+page.svelte`, `(app)/workspace/models/edit/+page.svelte`, `(app)/workspace/prompts/+page.svelte`, `(app)/workspace/prompts/[id]/+page.svelte`, `(app)/workspace/prompts/create/+page.svelte`, `(app)/workspace/skills/+page.svelte`, `(app)/workspace/skills/create/+page.svelte`, `(app)/workspace/skills/edit/+page.svelte`, `(app)/workspace/tools/+page.svelte`, `(app)/workspace/tools/create/+page.svelte`, `(app)/workspace/tools/edit/+page.svelte`, `auth/+page.svelte`, `error/+page.svelte`, `s/[id]/+page.svelte`, `watch/+page.svelte`

## Frontend API client modules (src/lib/apis) — 29 items

- `analytics`
- `audio`
- `auths`
- `automations`
- `calendar`
- `channels`
- `chats`
- `configs`
- `evaluations`
- `files`
- `folders`
- `functions`
- `groups`
- `images`
- `knowledge`
- `memories`
- `models`
- `notes`
- `notifications`
- `ollama`
- `openai`
- `prompts`
- `retrieval`
- `skills`
- `streaming`
- `terminal`
- `tools`
- `users`
- `utils`

## Admin settings panels (src/lib/components/admin/Settings) — 18 items

- `Audio`
- `Authentication`
- `CodeExecution`
- `Connections`
- `Database`
- `Documents`
- `Evaluations`
- `Events`
- `ExternalKnowledge`
- `General`
- `I18nSettings`
- `Images`
- `Integrations`
- `Interface`
- `Models`
- `Pipelines`
- `Subagents`
- `WebSearch`

## User settings panels (src/lib/components/chat/Settings) — 14 items

- `About`
- `Account`
- `ArchivedChats`
- `Audio`
- `Connections`
- `DataControls`
- `General`
- `Integrations`
- `Interface`
- `Notifications`
- `Personalization`
- `Shortcuts`
- `SyncStatsModal`
- `Usage`

## Docker Compose files (.) — 8 items

- `docker-compose.a1111-test.yaml`
- `docker-compose.amdgpu.yaml`
- `docker-compose.api.yaml`
- `docker-compose.data.yaml`
- `docker-compose.gpu.yaml`
- `docker-compose.otel.yaml`
- `docker-compose.playwright.yaml`
- `docker-compose.yaml`

## CI workflows (.github/workflows) — 10 items

- `backend.yaml`
- `codespell.disabled`
- `docker.yaml`
- `frontend.yaml`
- `issue-label.yaml`
- `lint-backend.disabled`
- `lint-frontend.disabled`
- `regression.yaml`
- `release-pypi.yml`
- `release.yml`

## Repository scripts (scripts) — 2 items

- `generate-sbom.sh`
- `prepare-pyodide.js`

## Scale

| What | Count |
|---|---|
| Alembic migration files | 58 |
| Backend Python files (backend/open_webui) | 263 |
| Model (repository) files | 26 |
| Utility modules (backend/open_webui/utils, recursive) | 60 |
| Svelte components (src, recursive) | 671 |
| Icon components | 182 |
| Translation locales | 64 |
| Backend test files | 0 |
