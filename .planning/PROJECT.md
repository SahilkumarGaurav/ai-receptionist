# AI Dental Receptionist — Private Doctor Dashboard MVP

## What This Is

A private, modern doctor dashboard for an existing AI Dental Receptionist system. The dashboard integrates with the existing Python `main.py` backend (Deepgram-based voice AI receptionist) to display and manage patient appointments booked through the AI phone agent. Dentists can securely log in, view upcoming appointments, confirm/reject pending bookings, and track appointment status — all in real-time as the AI receptionist creates them.

## Core Value

Dentists can instantly see and manage every appointment booked by the AI receptionist without leaving their chair — no manual entry, no missed bookings, no double-booking.

## Requirements

### Validated

- ✓ AI voice receptionist handles patient calls via Deepgram (existing — main.py)
- ✓ Patient name, service, date/time collection via voice (existing — receptionist_functions.py)
- ✓ Relative date parsing (today, tomorrow, next Monday, etc.) (existing)
- ✓ Service catalog with durations (cleaning, checkup, filling, crown, root canal, extraction, whitening, consultation) (existing)

### Active

- [ ] Private doctor login at `/login` with session-based auth
- [ ] Dashboard at `/dashboard` showing today's appointments, pending count, confirmed count, upcoming list
- [ ] Appointments page at `/appointments` with full table (ID, patient, date, time, service, status)
- [ ] Status badges: Pending, Confirmed, Rejected, Cancelled, Completed
- [ ] Confirm action: pending → confirmed, updates backend, refreshes UI
- [ ] Reject action: pending → rejected, updates backend, refreshes UI
- [ ] Cancel action: confirmed → cancelled, updates backend, refreshes UI
- [ ] Complete action: confirmed → completed, updates backend, refreshes UI
- [ ] Patient info display: name, phone, email, date, time, service
- [ ] Backend API: GET /api/appointments, POST /api/appointments, PATCH /api/appointments/{id}/confirm|reject|cancel|complete
- [ ] Appointment data model: id, patient_name, phone, email, date, time, service, status, created_at
- [ ] Polling-based auto-refresh (5-10 seconds) for new appointments
- [ ] Loading states for all async actions
- [ ] Error handling with friendly messages
- [ ] Empty states for no appointments / no pending
- [ ] Responsive design (desktop, tablet, mobile)
- [ ] Professional medical SaaS UI (clean typography, rounded cards, clear badges, simple sidebar)
- [ ] Route protection: dashboard requires authentication
- [ ] API security: no secret exposure, request validation, data isolation

### Out of Scope

- Google Calendar integration — explicitly deferred per requirements
- Google OAuth — deferred
- WhatsApp/SMS notifications — deferred
- Payments/subscriptions — deferred
- Advanced analytics — deferred
- Detailed medical records/dental charts/X-rays — deferred
- Multi-clinic management — deferred
- Complex staff permissions — deferred
- AI call recordings — deferred
- Advanced notifications — deferred
- WebSockets — polling acceptable for MVP
- Rescheduling — explicitly excluded from MVP

## Context

- **Existing backend**: Python `main.py` uses Deepgram WebSocket API for real-time voice AI receptionist. Twilio integration for phone calls. Function calling via `receptionist_functions.py` for patient lookup, service info, date resolution.
- **Current appointment flow**: AI collects patient info → but no appointment creation/storage yet (functions are placeholders)
- **Tech stack**: Python 3.14, websockets, python-dotenv, tzdata. Deepgram for STT/TTS/LLM. No frontend yet.
- **Deployment**: Local development on port 5000 (WebSocket server)
- **Auth**: Simple session-based for MVP, replaceable with Firebase/Supabase later

## Constraints

- **Tech stack**: Must extend existing Python backend, not rewrite it. Frontend can be any modern framework.
- **Timeline**: MVP only — core booking visibility and management
- **Compatibility**: Must work with existing Deepgram/Twilio voice pipeline
- **Security**: No secrets in frontend. API keys stay in backend `.env`
- **Data isolation**: Single doctor for MVP (no multi-tenant yet)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extend existing `main.py` with REST API endpoints | Reuse Deepgram/Twilio infrastructure; avoid duplicate systems | — Pending |
| Simple session-based auth (cookie/JWT) for MVP | Fast to implement; replaceable with Firebase/Supabase later | — Pending |
| Polling (5-10s) instead of WebSockets for real-time | Simpler implementation; existing WebSocket used for voice only | — Pending |
| Single doctor / single clinic for MVP | Matches current backend architecture; multi-tenant later | — Pending |
| Frontend: Vanilla JS or lightweight framework (Alpine/Vue) | No build step complexity; easy to integrate with Python backend | — Pending |
| Appointment storage: JSON file or SQLite for MVP | Simple, no external DB dependency; migratable later | — Pending |

---

*Last updated: 2026-08-16 after initialization*