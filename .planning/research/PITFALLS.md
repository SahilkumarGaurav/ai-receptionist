# Pitfalls Research — AI Dental Receptionist Dashboard

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Context:** Greenfield frontend + brownfield backend extension
**Date:** 2026-08-16

---

## Critical Pitfalls

### 1. WebSocket + HTTP Server Conflict
**Warning Signs**: 
- "Address already in use" on port 5000
- WebSocket connections drop when HTTP requests come in
- Uvicorn fails to start with both protocols

**Prevention Strategy**:
- Use single Uvicorn process with FastAPI lifespan managing both
- FastAPI `WebSocketRoute` for existing Deepgram handler + `APIRoute` for REST
- Or: Keep existing `websockets.serve` in background task, add FastAPI on same port via `uvicorn.run` with custom lifespan

**Phase**: Phase 1 (Backend Foundation)

---

### 2. Deepgram Function Calling → HTTP API Bridge
**Warning Signs**:
- AI receptionist can't create appointments (function not found)
- Function call timeout errors in Deepgram logs
- Appointments created but not visible in dashboard

**Prevention Strategy**:
- Add `create_appointment` function to `receptionist_functions.py` that calls `POST /api/v1/appointments` via `httpx` (async)
- Ensure function returns appointment ID for AI confirmation
- Test function calling independently before integrating

**Phase**: Phase 1 (AI Integration)

---

### 3. Polling Race Conditions
**Warning Signs**:
- Dashboard shows stale data after action
- Double-booking appearance (same appointment twice)
- Status badge doesn't update after confirm/reject

**Prevention Strategy**:
- Use optimistic UI updates: update local state immediately, then sync with server
- Or: Force refetch after every action (simpler, acceptable for MVP)
- Add `ETag` or `Last-Modified` headers for conditional requests (optional)
- Disable action buttons during processing

**Phase**: Phase 2-3 (Frontend + Actions)

---

### 4. JWT Cookie Not Sent Cross-Origin
**Warning Signs**:
- Login succeeds but dashboard shows "unauthorized"
- Cookie visible in DevTools but not sent with API calls
- CORS errors on authenticated requests

**Prevention Strategy**:
- Set `SameSite=Lax` (not `Strict`) for localhost development
- Ensure `credentials: 'include'` in fetch calls
- CORS middleware: `allow_credentials=True`, `allow_origins=["http://localhost:5000"]`
- Use HttpOnly + Secure (Secure only in production)

**Phase**: Phase 1 (Auth)

---

### 5. SQLite Concurrency with Async
**Warning Signs**:
- "Database is locked" errors under load
- Slow queries blocking event loop
- Connection leaks

**Prevention Strategy**:
- Use `aiosqlite` with connection pool (single connection for MVP is fine)
- Enable WAL mode: `PRAGMA journal_mode=WAL;`
- Keep transactions short
- Close connections properly in lifespan shutdown

**Phase**: Phase 1 (Data Layer)

---

### 6. Timezone Handling Inconsistency
**Warning Signs**:
- Appointments show wrong date/time on dashboard
- "Today's appointments" count incorrect
- AI books for wrong day

**Prevention Strategy**:
- Store all datetimes in UTC in database
- Use existing `get_timezone()` from `receptionist_functions.py` for display
- Frontend: receive UTC, convert to clinic timezone for display
- Single source of truth: `TIMEZONE` env var

**Phase**: Phase 1-2 (Data Model + Dashboard)

---

### 7. Breaking Existing Voice AI Flow
**Warning Signs**:
- Deepgram connection fails after changes
- Function calling stops working
- Audio streaming breaks

**Prevention Strategy**:
- **Do not modify** `sts_connect`, `twilio_handler`, `sts_sender`, `sts_receiver`, `twilio_receiver`
- Add FastAPI as **addition**, not replacement
- Test voice flow after every backend change
- Keep existing `websockets.serve` running in background task

**Phase**: All phases — continuous validation

---

### 8. Frontend Served from Same Port as WebSocket
**Warning Signs**:
- Static files not found
- WebSocket upgrade fails on static file requests
- MIME type errors for JS/CSS

**Prevention Strategy**:
- FastAPI `StaticFiles` at `/static` with `html=True`
- Root `/` redirects to `/login` or `/dashboard`
- WebSocket routes at `/ws` or keep existing `/` for WS, serve frontend at `/app`
- Test both WS and HTTP on same port

**Phase**: Phase 1 (Backend + Frontend Serving)

---

## Common Mistakes

### 9. Over-Engineering Auth for MVP
**Warning Signs**: Building refresh tokens, email verification, OAuth before basic login works
**Prevention**: Simple JWT in cookie, 8-hour expiry, bcrypt passwords. Replace in v2.
**Phase**: Phase 1

### 10. Ignoring Mobile Usability
**Warning Signs**: Dashboard unusable on phone; buttons too small; table scrolls poorly
**Prevention**: Test on mobile from day one; Tailwind responsive utilities; card layout on mobile, table on desktop
**Phase**: Phase 2

### 11. Hardcoding Service List in Frontend
**Warning Signs**: New service added in backend but not in frontend dropdown/badge
**Prevention**: Single source of truth — fetch services from API or share constants file
**Phase**: Phase 1-2

### 12. No Error Boundaries in Polling
**Warning Signs**: Dashboard freezes when backend restarts; console errors spam
**Prevention**: Try/catch in poll loop; exponential backoff; show "Reconnecting..." banner
**Phase**: Phase 2

---

## Phase Mapping Summary

| Pitfall | Primary Phase | Validation |
|---------|---------------|------------|
| WebSocket + HTTP conflict | Phase 1 | Voice call + API both work |
| Function calling bridge | Phase 1 | AI creates appointment visible in DB |
| Polling race conditions | Phase 2-3 | Actions update UI instantly |
| JWT cookie issues | Phase 1 | Login → Dashboard works |
| SQLite concurrency | Phase 1 | Concurrent polls don't lock |
| Timezone inconsistency | Phase 1-2 | Times match across AI/DB/UI |
| Breaking voice AI | All | Voice test passes each phase |
| Static file serving | Phase 1 | Frontend loads, WS connects |
| Over-engineering auth | Phase 1 | Login works in <5 min |
| Mobile usability | Phase 2 | Dashboard usable on phone |
| Hardcoded services | Phase 1-2 | Services sync automatically |
| Polling error handling | Phase 2 | Backend restart handled gracefully |

---

## Prevention Checklist (Run Each Phase)

- [ ] Voice AI test: Make test call, verify booking flow
- [ ] API test: `curl` all endpoints, verify responses
- [ ] Frontend test: Login → Dashboard → Actions → Logout
- [ ] Mobile test: Chrome DevTools device toolbar
- [ ] Concurrency test: Multiple dashboard tabs + API calls
- [ ] Timezone test: Verify UTC storage, local display