---
phase: 1
slug: backend-foundation-ai-integration
mode: mvp
waves: 3
created: 2026-08-16
status: planned
---

# Phase 1 Plan: Backend Foundation & AI Integration

**Goal:** Extend `main.py` with FastAPI, SQLite, Auth, and appointment CRUD; connect AI receptionist to create appointments
**Mode:** MVP — Vertical slice delivering end-to-end working flow
**Requirements:** AUTH-01–05, API-01–10, MODEL-01–10, AI-01, AI-03, SEC-01–05

---

## Wave 1: Database & Authentication Foundation

### Plan 01-01: Database Schema & Connection

**Objective:** Create SQLite database with appointments/users tables, WAL mode, and async connection management in FastAPI lifespan.

**Wave:** 1
**Depends on:** —
**Requirements:** MODEL-01, MODEL-02, MODEL-03, MODEL-04, MODEL-05, MODEL-06, MODEL-07, MODEL-08, MODEL-09, MODEL-10
**Files modified:** `main.py`, `database.py` (new)
**Autonomous:** true

<read_first>
- `main.py` — existing WebSocket server, lifespan pattern
- `.planning/research/STACK.md` — aiosqlite patterns
- `.planning/research/ARCHITECTURE.md` — data layer design
</read_first>

<action>
1. Create `database.py` with:
   - `init_db()` — creates tables, enables WAL mode, foreign keys
   - `get_db()` — async generator dependency for FastAPI
   - `close_db()` — cleanup on shutdown
   - Table schemas per RESEARCH.md (users, appointments with indexes)
2. Modify `main.py`:
   - Add FastAPI import and app creation
   - Add lifespan context manager that calls `init_db()` on startup, `close_db()` on shutdown
   - Keep existing `websockets.serve` in background task within lifespan
   - Mount FastAPI on same port via `uvicorn.run`
3. Add `aiosqlite` to `pyproject.toml` dependencies
4. Run `uv sync` to install
</action>

<acceptance_criteria>
- `uv run python -c "import database; import asyncio; asyncio.run(database.init_db())"` creates `appointments.db` with both tables
- `PRAGMA journal_mode;` returns `wal`
- `PRAGMA foreign_keys;` returns `1`
- Tables have correct columns and indexes per schema
- Existing WebSocket server still starts on port 5000
</acceptance_criteria>

---

### Plan 01-02: JWT Authentication System

**Objective:** Implement login/logout with HttpOnly JWT cookies, bcrypt password hashing, and auth middleware.

**Wave:** 1
**Depends on:** 01-01
**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, SEC-01, SEC-02, SEC-03, SEC-04
**Files modified:** `main.py`, `auth.py` (new), `pyproject.toml`
**Autonomous:** true

<read_first>
- `main.py` — FastAPI app, lifespan
- `.planning/research/STACK.md` — python-jose, passlib patterns
- `.planning/research/PITFALLS.md` — JWT cookie pitfalls (SameSite=lax)
- `.env.example` (create if missing) — JWT_SECRET, DOCTOR_EMAIL, DOCTOR_PASSWORD
</read_first>

<action>
1. Create `auth.py` with:
   - `hash_password(password: str) -> str` using passlib bcrypt
   - `verify_password(password: str, hash: str) -> bool`
   - `create_access_token(data: dict) -> str` — JWT with 8hr expiry, HS256
   - `decode_token(token: str) -> dict` — validates and returns payload
   - `get_current_user(request: Request) -> dict` — FastAPI dependency, reads cookie
   - `seed_default_user(db)` — creates doctor from env vars on startup
2. Add auth endpoints to `main.py`:
   - `POST /api/v1/auth/login` — validates credentials, sets HttpOnly cookie
   - `POST /api/v1/auth/logout` — clears cookie
   - `GET /api/v1/auth/me` — returns current user (protected)
3. Add CORS middleware with `allow_credentials=True`, `allow_origins=["http://localhost:5000"]`
4. Add `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart` to `pyproject.toml`
5. Run `uv sync`
6. Create `.env.example` with required vars
</action>

<acceptance_criteria>
- `POST /api/v1/auth/login` with correct credentials returns 200, sets `access_token` cookie (HttpOnly, SameSite=lax, max-age=28800)
- `POST /api/v1/auth/login` with wrong password returns 401
- `GET /api/v1/auth/me` with valid cookie returns user info
- `GET /api/v1/auth/me` without cookie returns 401
- `POST /api/v1/auth/logout` clears cookie
- Default doctor user created in DB on startup from env vars
- Password stored as bcrypt hash (not plaintext)
</acceptance_criteria>

---

## Wave 2: Appointment CRUD API

### Plan 01-03: Appointment Pydantic Models & Database Operations

**Objective:** Define request/response models and async DB operations for appointments.

**Wave:** 2
**Depends on:** 01-01
**Requirements:** MODEL-01..10, API-07, API-08, API-10
**Files modified:** `models.py` (new), `crud.py` (new)
**Autonomous:** true

<read_first>
- `database.py` — get_db dependency
- `.planning/research/STACK.md` — Pydantic v2 patterns
- `.planning/REQUIREMENTS.md` — MODEL-01..10, API-07, API-08, API-10
- `.planning/research/ARCHITECTURE.md` — data model
</read_first>

<action>
1. Create `models.py` with:
   - `AppointmentCreate` — patient_name, phone, email?, date, time, service
   - `AppointmentResponse` — all fields + id, status, created_at, updated_at
   - `AppointmentListResponse` — list wrapper
   - `StatusTransition` — for confirm/reject/cancel/complete (empty body)
   - `ErrorResponse` — standard error format
   - Service enum: cleaning, checkup, filling, crown, root_canal, extraction, whitening, consultation
2. Create `crud.py` with async functions:
   - `create_appointment(db, data: AppointmentCreate) -> AppointmentResponse`
   - `get_appointments(db, status: str | None = None) -> list[AppointmentResponse]`
   - `get_appointment(db, id: str) -> AppointmentResponse | None`
   - `update_status(db, id: str, status: str) -> AppointmentResponse`
   - All use parameterized queries (no string interpolation)
</action>

<acceptance_criteria>
- `AppointmentCreate` validates: required fields, phone pattern, date/time format, service enum
- `create_appointment` inserts row, returns response with generated UUID
- `get_appointments` returns all, optional status filter works
- `get_appointment` returns 404-equivalent (None) for missing ID
- `update_status` only allows valid transitions (pending→confirmed/rejected, confirmed→cancelled/completed)
- All SQL uses `?` placeholders (no f-strings in queries)
</acceptance_criteria>

---

### Plan 01-04: Appointment REST Endpoints

**Objective:** Implement all 6 API endpoints with auth protection and consistent error handling.

**Wave:** 2
**Depends on:** 01-02, 01-03
**Requirements:** API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, API-09, API-10, SEC-05
**Files modified:** `main.py`, `api_appointments.py` (new)
**Autonomous:** true

<read_first>
- `main.py` — FastAPI app, auth dependency
- `auth.py` — get_current_user
- `crud.py` — appointment operations
- `models.py` — request/response models
- `.planning/research/ARCHITECTURE.md` — API endpoint specs
</read_first>

<action>
1. Create `api_appointments.py` with router:
   - `GET /api/v1/appointments` — optional `?status=` query, returns list
   - `POST /api/v1/appointments` — creates appointment, defaults status=pending
   - `PATCH /api/v1/appointments/{id}/confirm` — status=confirmed
   - `PATCH /api/v1/appointments/{id}/reject` — status=rejected
   - `PATCH /api/v1/appointments/{id}/cancel` — status=cancelled
   - `PATCH /api/v1/appointments/{id}/complete` — status=completed
2. All endpoints:
   - Require `get_current_user` dependency (except POST for AI bridge)
   - Return `AppointmentResponse` or list
   - Raise `HTTPException(404)` if not found
   - Raise `HTTPException(400)` for invalid status transition
3. Register router in `main.py` with prefix `/api/v1`
4. Add global exception handler for consistent error format
</action>

<acceptance_criteria>
- `GET /api/v1/appointments` returns 200 + list (empty array if none)
- `GET /api/v1/appointments?status=pending` filters correctly
- `POST /api/v1/appointments` with valid data returns 201 + appointment (status=pending)
- `POST /api/v1/appointments` with invalid data returns 400 + error detail
- `PATCH /confirm|reject|cancel|complete` on valid ID returns 200 + updated appointment
- `PATCH` on invalid ID returns 404
- `PATCH` with invalid transition (e.g., confirmed→confirmed) returns 400
- All protected endpoints return 401 without valid cookie
- Error responses: `{"error": "...", "status_code": N}`
</acceptance_criteria>

---

## Wave 3: AI Receptionist Integration & Verification

### Plan 01-05: AI Appointment Creation Bridge

**Objective:** Add `create_appointment` function to receptionist_functions.py callable from Deepgram.

**Wave:** 3
**Depends on:** 01-04
**Requirements:** AI-01, AI-03, MODEL-01..10
**Files modified:** `receptionist_functions.py`, `config.json`, `main.py` (import), `pyproject.toml`
**Autonomous:** true

<read_first>
- `receptionist_functions.py` — existing FUNCTION_MAP, pattern for async functions
- `config.json` — functions array format
- `main.py` — FastAPI app running on :5000
- `.planning/research/PITFALLS.md` — AI bridge pitfalls
- `.planning/REQUIREMENTS.md` — AI-01, AI-03
</read_first>

<action>
1. Add `httpx` to `pyproject.toml` (if not already), run `uv sync`
2. In `receptionist_functions.py`:
   - Add `async def create_appointment(patient_name, phone, date, time, service, email=None)`
   - Function calls `POST http://localhost:5000/api/v1/appointments` via `httpx.AsyncClient`
   - Returns `{"appointment_id": "...", "status": "pending", "message": "..."}`
   - Handle errors: network, 400, 401, 500 → return error dict
   - Add to `FUNCTION_MAP`
3. In `config.json`:
   - Add function definition for `create_appointment` with parameters matching function signature
   - Include description for LLM: when to call, parameter details
4. Ensure `main.py` imports updated `FUNCTION_MAP`
</action>

<acceptance_criteria>
- `create_appointment` function exists in `FUNCTION_MAP`
- Function is async, uses httpx to call local API
- `config.json` has correct function schema (name, description, parameters)
- Function returns appointment_id on success
- Function returns error dict on failure (not exception)
- Deepgram function calling can invoke it (tested in integration)
</acceptance_criteria>

---

### Plan 01-06: Integration Test & Verification

**Objective:** Verify end-to-end flow: voice AI → appointment creation → API retrieval, and existing voice flow unbroken.

**Wave:** 3
**Depends on:** 01-01, 01-02, 01-04, 01-05
**Requirements:** All Phase 1 requirements
**Files modified:** `tests/` (new), `pytest.ini` (new)
**Autonomous:** true

<read_first>
- `main.py` — complete application
- `.planning/phases/01-backend-foundation-ai-integration/01-VALIDATION.md` — verification map
- `.planning/research/PITFALLS.md` — regression test requirements
</read_first>

<action>
1. Create `pytest.ini` with asyncio mode, test paths
2. Create `tests/conftest.py` with fixtures:
   - `app` — FastAPI TestClient
   - `db` — test database (separate file)
   - `auth_headers` — login cookie for authenticated requests
3. Create test files per VALIDATION.md Wave 0:
   - `test_db.py` — schema, WAL, CRUD
   - `test_auth.py` — login, logout, cookie, JWT
   - `test_api.py` — all endpoints, validation, status codes
   - `test_ai_bridge.py` — create_appointment function
   - `test_integration.py` — WebSocket + HTTP coexistence
4. Run `uv run pytest tests/ -v` — all pass
5. Manual regression test:
   - Start server: `uv run python main.py`
   - Make test call to Twilio/Deepgram (or simulate)
   - Verify appointment created in DB
   - Verify `GET /api/v1/appointments` returns it
</action>

<acceptance_criteria>
- `uv run pytest tests/ -v` exits 0 (all tests pass)
- Test coverage includes all 23 Phase 1 requirements
- Manual voice AI test: appointment appears in DB within 1 second
- Existing WebSocket connection works (Deepgram connects, audio streams)
- No errors in server logs during voice flow
- Server handles concurrent HTTP polling + WebSocket voice
</acceptance_criteria>

---

## Must-Haves for Phase Verification

Per ROADMAP.md success criteria:
1. ✅ Voice AI creates appointment → visible in SQLite DB within 1 second
2. ✅ All 6 API endpoints return correct JSON responses
3. ✅ Doctor can log in at `/login` → receives HttpOnly JWT cookie → accesses `/dashboard`
4. ✅ Existing Deepgram/Twilio voice flow works identically after changes

---

## Risk Mitigation

| Risk | Plan Task | Mitigation |
|------|-----------|------------|
| WebSocket + HTTP conflict | 01-01, 01-06 | Background task pattern; integration test validates both |
| AI function calling fails | 01-05 | Unit test with mock server; integration test with real API |
| JWT cookie issues | 01-02 | SameSite=lax, test in incognito, credentials:include |
| SQLite locking | 01-01 | WAL mode, single connection, short transactions |
| Breaking voice AI | 01-06 | Regression test mandatory before commit |

---

*Plan created: 2026-08-16*
*Planner: gsd-planner (manual)*