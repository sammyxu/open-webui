# Websockets, Real-Time Events and Redis

## At a Glance

- *Provisional; refined at the end of research.*
- The browser keeps one Socket.IO connection to the backend at `/ws/socket.io`; streamed replies,
  status updates, channel messages, note collaboration and notifications travel over it.
- The server tracks connected users, sessions and model usage in in-memory pools (or Redis when
  `WEBSOCKET_MANAGER=redis`), cleaned up by periodic background loops in every worker.
- Redis is optional; without it, more than one worker or replica cannot share live events, task
  stops, sign-out revocation or rate-limit counters.
