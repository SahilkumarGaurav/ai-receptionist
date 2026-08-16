# Walking Skeleton — AI Dental Receptionist Dashboard

**Phase:** 1
**Generated:** 2026-08-16

## Capability Proven End-to-End

A dentist can log in to a private dashboard and see a patient appointment created in real-time by the AI voice receptionist during a phone call.

## Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Framework | FastAPI + Uvicorn (extend existing `main.py`) | Reuses Deepgram/Twilio WebSocket infrastructure; single process |
| Data Layer | SQLite + aiosqlite (WAL mode) | Zero-config for MVP; migratable to PostgreSQL |
| Auth | JWT in HttpOnly cookies + bcrypt | Simple, replaceable with Firebase/Supabase later |
| Frontend | Alpine.js + Tailwind CDN (static files via FastAPI) | No build step; medical SaaS aesthetic; served from same origin |
| Deployment | Local development on port 5000 | Matches existing voice AI port; no external deps |
| Directory Layout | Single `main.py` with modular imports (`database.py`, `auth.py`, `crud.py`, `models.py`, `api_appointments.py`) | Minimal files; clear separation; easy to extract later |

## Stack Touched in Phase 1

- [x] Project scaffold — FastAPI app integrated with existing WebSocket server
- [x] Routing — `/api/v1/auth/*`, `/api/v1/appointments*`, static files at `/static`
- [x] Database — SQLite with users & appointments tables; real read (GET) and write (POST/PATCH)
- [x] AI Integration — `create_appointment` function callable from Deepgram
- [x] Deployment — `uv run python main.py` runs full stack (WebSocket + HTTP) on localhost:5000

## Out of Scope (Deferred to Later Slices)

- Frontend UI (Phase 2: login page, dashboard, appointments table)
- Appointment actions UI (Phase 3: confirm/reject/cancel/complete buttons)
- Patient management page (disabled in sidebar)
- Settings page (disabled in sidebar)
- Google Calendar integration
- WhatsApp/SMS notifications
- Multi-clinic / multi-doctor support
- WebSocket real-time updates (polling sufficient for MVP)
- Production deployment (Docker, CI/CD, PostgreSQL)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- **Phase 2:** Frontend Core — Login page, Dashboard with polling, Appointments table, medical SaaS UI, responsive design
- **Phase 3:** Appointment Actions — Confirm, Reject, Cancel, Complete buttons with optimistic updates and toast notifications
- **Phase 4+:** v2 features (Calendar, Notifications, Analytics, Multi-clinic, etc.)

---

*Skeleton recorded: 2026-08-16*