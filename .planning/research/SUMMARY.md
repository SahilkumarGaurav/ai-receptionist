# Research Summary — AI Dental Receptionist Dashboard

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Date:** 2026-08-16

---

## Key Findings

### Stack (from STACK.md)

**Backend**: Extend existing Python with **FastAPI + Uvicorn** on same port as WebSocket server. Add **SQLite + aiosqlite** for appointments, **JWT + bcrypt** for auth, **Pydantic** for validation.

**Frontend**: **Alpine.js + Tailwind CSS via CDN** — no build step, served as static files by FastAPI. Lightweight, medical SaaS aesthetic achievable.

**Not Using**: React/Next.js (overkill), PostgreSQL (overkill), WebSockets for dashboard (polling sufficient), Firebase/Supabase (deferred to v2).

### Table Stakes (from FEATURES.md)

**52 v1 requirements** across 8 categories:
- Authentication (5): Login, session, logout, route protection, timeout
- Dashboard Overview (9): Counts, upcoming table, polling, loading, errors, empty states
- Appointments Management (7): Full table, status badges, polling, states
- Appointment Actions (8): Confirm/Reject/Cancel/Complete with loading/disabled/optimistic updates
- Patient Info (5): Name, phone, email, service, date/time
- Backend API (10): CRUD + status transitions + validation + security
- Data Model (10): Fields + service enum
- AI Integration (3): POST from AI, polling visibility, pending default
- UI/UX (7): Medical SaaS design, sidebar, responsive, polish
- Security (5): Route protection, validation, no secrets, isolation

### Architecture (from ARCHITECTURE.md)

**Component Boundaries**:
1. Voice AI (existing) → calls `POST /api/appointments`
2. REST API (new FastAPI) → SQLite + JWT auth
3. Frontend (Alpine.js) → polls `GET /api/appointments` every 5-10s

**Data Flow**: Patient call → AI collects info → AI calls API → Dashboard polls → Doctor acts → API updates → Dashboard refreshes

**Build Order**: Schema → FastAPI + Uvicorn → Auth → CRUD API → AI integration → Login → Dashboard → Appointments page → Actions → Polish

### Watch Out For (from PITFALLS.md)

| # | Pitfall | Prevention | Phase |
|---|---------|------------|-------|
| 1 | WebSocket + HTTP conflict | Single Uvicorn with lifespan managing both | 1 |
| 2 | Deepgram function → HTTP bridge | Add `create_appointment` function using `httpx` | 1 |
| 3 | Polling race conditions | Optimistic updates or forced refetch; disable buttons | 2-3 |
| 4 | JWT cookie cross-origin | `SameSite=Lax`, `credentials: 'include'`, CORS config | 1 |
| 5 | SQLite async locking | WAL mode, short transactions, aiosqlite | 1 |
| 6 | Timezone inconsistency | UTC storage, clinic TZ display, single `TIMEZONE` env | 1-2 |
| 7 | Breaking voice AI | Don't modify existing WS handlers; add FastAPI alongside | All |
| 8 | Static file serving on WS port | FastAPI StaticFiles at `/static`, root redirects | 1 |

---

## Confidence Assessment

| Area | Confidence | Risk Mitigation |
|------|------------|-----------------|
| Backend extension | 95% | Proven FastAPI + WebSocket coexistence patterns |
| Frontend simplicity | 85% | Alpine.js less common; have Vue CDN backup |
| AI integration | 90% | Function calling pattern established in existing code |
| Polling architecture | 90% | Simple, meets 10s requirement |
| Auth simplicity | 95% | JWT cookie standard pattern |
| Mobile responsiveness | 80% | Tailwind responsive utilities; test early |

---

## Next Steps

1. **Phase 1**: Backend foundation (schema, FastAPI, auth, CRUD, AI bridge)
2. **Phase 2**: Frontend core (login, dashboard, appointments, polling, states)
3. **Phase 3**: Actions (confirm, reject, cancel, complete with UI feedback)

Each phase maps to requirements in REQUIREMENTS.md traceability table.