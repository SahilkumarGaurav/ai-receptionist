# Architecture Research — AI Dental Receptionist Dashboard

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Context:** Greenfield frontend + brownfield backend extension
**Date:** 2026-08-16

---

## System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Patient       │────▶│  AI Receptionist │────▶│  Backend API    │
│   (Phone Call)  │     │  (Deepgram +     │     │  (FastAPI +     │
│                 │     │   Twilio)        │     │   SQLite)       │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Doctor        │◀────│  Dashboard UI    │◀────│  Polling (5-10s)│
│   (Browser)     │     │  (Alpine.js +    │     │                 │
│                 │     │   Tailwind)      │     └─────────────────┘
└─────────────────┘     └──────────────────┘
```

---

## Component Boundaries

### 1. Voice AI Layer (Existing — Do Not Modify)
- **File**: `main.py`, `receptionist_functions.py`, `config.json`
- **Responsibility**: Deepgram WebSocket connection, Twilio audio streaming, function calling
- **Interface**: Calls `POST /api/appointments` when booking confirmed
- **Port**: 5000 (WebSocket)

### 2. REST API Layer (New — Extend main.py)
- **Framework**: FastAPI mounted on same Uvicorn server
- **Routes**: `/api/v1/*`
- **Auth**: JWT bearer tokens (optional for MVP, required for production)
- **Endpoints**:
  - `GET /appointments` — list all
  - `POST /appointments` — create (AI receptionist)
  - `PATCH /appointments/{id}/confirm|reject|cancel|complete` — status transitions

### 3. Data Layer (New)
- **Storage**: SQLite (`appointments.db`)
- **Schema**: `appointments` table + `users` table
- **Access**: aiosqlite async connection pool
- **Models**: Pydantic for validation, SQLAlchemy Core or raw SQL for queries

### 4. Auth Layer (New)
- **Mechanism**: JWT in HttpOnly cookie + bcrypt password hash
- **Flow**: Login → set cookie → middleware validates on protected routes
- **Session**: 8-hour expiry, refresh on activity

### 5. Frontend Layer (New)
- **Served**: Static files via FastAPI `StaticFiles` at `/static`
- **Entry**: `index.html` at `/` (redirects to `/login` or `/dashboard`)
- **Framework**: Alpine.js (CDN) + Tailwind CSS (CDN)
- **Pages**: `/login`, `/dashboard`, `/appointments`
- **State**: Alpine.js reactive data + polling interval

---

## Data Flow

### Appointment Creation (AI → Dashboard)
```
1. Patient calls → Deepgram STT → LLM → Function calls
2. AI collects: name, phone, service, date, time
3. AI calls resolve_relative_date() → YYYY-MM-DD
4. AI confirms with patient
4. main.py executes: POST /api/v1/appointments {patient_name, phone, email?, date, time, service, status: "pending"}
5. API validates → inserts into SQLite → returns appointment with ID
6. Dashboard polling (GET /api/v1/appointments) → receives new appointment within 5-10s
7. Dashboard renders in upcoming table with "Pending" badge
```

### Appointment Confirmation (Doctor → Backend)
```
1. Doctor clicks "Confirm" on pending appointment
2. Frontend: PATCH /api/v1/appointments/{id}/confirm
3. API: validates auth, finds appointment, updates status → "confirmed"
4. API returns updated appointment
5. Frontend: optimistic update or refetch → badge turns green "Confirmed"
6. Next poll: all clients see confirmed status
```

---

## Suggested Build Order

| Order | Component | Reason |
|-------|-----------|--------|
| 1 | SQLite schema + models | Foundation for all API endpoints |
| 2 | FastAPI app + Uvicorn integration | Mount on existing server |
| 3 | Auth system (login, JWT, middleware) | Protects all subsequent endpoints |
| 4 | Appointment CRUD API | Core data operations |
| 5 | AI integration (POST /appointments) | Connects existing voice AI |
| 6 | Frontend: login page + auth flow | Entry point |
| 7 | Frontend: dashboard + polling | Primary view |
| 8 | Frontend: appointments page | Full management |
| 9 | Frontend: action buttons + status transitions | Core workflow |
| 10 | Polish: loading, errors, empty states, responsive | MVP completeness |

---

## Integration Points with Existing Code

| Existing | Integration Point | Change Required |
|----------|-------------------|-----------------|
| `main.py` | Add FastAPI routes + lifespan | Modify: add FastAPI app, mount static files, run both WS + HTTP |
| `receptionist_functions.py` | Add `create_appointment` function | Add: new function in FUNCTION_MAP, calls POST /api/appointments |
| `config.json` | No change needed | — |
| `pyproject.toml` | Add dependencies | Modify: fastapi, uvicorn, python-jose, passlib, aiosqlite, pydantic |

---

## Security Boundaries

- **Frontend**: No secrets, no API keys, only JWT cookie
- **Backend**: `.env` for DEEPGRAM_API_KEY, JWT_SECRET, DATABASE_URL
- **Database**: Local SQLite file, not exposed
- **API**: CORS restricted to frontend origin (localhost:5000)
- **Auth**: HttpOnly Secure SameSite=Strict cookies

---

## Scalability Considerations (Post-MVP)

| Current | Future |
|---------|--------|
| SQLite | PostgreSQL |
| Polling | WebSocket / SSE |
| Single doctor | Multi-tenant (clinic_id) |
| In-process | Separate API service |
| File-based static | CDN / Nginx |