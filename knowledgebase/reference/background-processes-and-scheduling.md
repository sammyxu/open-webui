# Background Processes and Scheduling

## At a Glance

- MedIT GPT has **no crontab and no separate worker process**. Everything that runs without a click
  is an asyncio task inside each uvicorn worker, started by `lifespan` in
  `backend/open_webui/main.py`, or a background task spawned from a chat request.
- Periodic loops: session and usage pool clean-up (websocket presence), the automations scheduler
  (automations, timers, calendar alerts), and, only when Redis is configured, task-command,
  heartbeat and websocket-event listeners.
- Per-chat background work (title, tags, follow-ups, memory review) is spawned when a chat response
  finishes, not on a schedule.
- *Provisional summary; refined at the end of the research.*
