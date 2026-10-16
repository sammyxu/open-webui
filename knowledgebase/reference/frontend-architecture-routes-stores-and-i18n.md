# Front-End Architecture, Routes, Stores and Translations

## At a Glance

- MedIT GPT's browser interface is a single-page SvelteKit application served as static files by
  the backend; every page URL is handled in the browser, and the backend only answers `/api`,
  `/ollama`, `/openai`, `/oauth` and `/ws` requests (provisional; see sections 2 and 5).
- The root layout boots the app: it fetches the backend configuration, starts translations, opens
  the websocket and checks the session; when the backend cannot be reached it shows the
  **Backend Required** screen (provisional; see section 5).
- Admin settings and analytics are no longer separate pages: `/admin/settings`,
  `/admin/settings/<tab>` and `/admin/analytics` redirect to the shared Settings window at
  `/?settings=admin:<tab>` (provisional; see section 2).
- Interface text is translated with i18next. Plain keys are the English text itself; dotted
  settings keys have English text only in `en-US` and other languages fall back to it
  (provisional; see sections 4 and 7).
