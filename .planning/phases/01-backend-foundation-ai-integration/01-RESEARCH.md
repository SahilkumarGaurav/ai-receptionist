# Phase 1 Research: Backend Foundation & AI Integration

**Phase:** 1 — Backend Foundation & AI Integration
**Goal:** Extend `main.py` with FastAPI, SQLite, Auth, and appointment CRUD; connect AI receptionist to create appointments
**Mode:** MVP (Vertical slice — end-to-end working slice)
**Requirements:** AUTH-01–05, API-01–10, MODEL-01–10, AI-01, AI-03, SEC-01–05

---

## Research Questions

### 1. FastAPI + WebSocket Coexistence on Same Port
**Question:** How to run FastAPI HTTP routes alongside existing `websockets.serve` on port 5000 without conflicts?

**Findings:**
- **Option A: Single Uvicorn with lifespan** — Mount existing WebSocket handler as `WebSocketRoute` in FastAPI, run everything under one Uvicorn process. Cleanest but requires refactoring `main.py` WebSocket handler to ASGI style.
- **Option B: Background task** — Keep existing `websockets.serve` running in `asyncio.create_task()` within FastAPI lifespan, add FastAPI routes on same port via `uvicorn.run(app, port=5000)`. Simpler, less invasive.
- **Option C: Separate ports** — Run WebSocket on 5000, FastAPI on 5001. Requires CORS config, more complex for frontend.

**Recommendation:** Option B (background task). Minimal changes to existing working voice AI code. FastAPI lifespan manages both:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start existing WebSocket server in background
    ws_task = asyncio.create_task(websockets.serve(twilio_handler, "localhost", 5000))
    # Initialize DB connection
    yield
    ws_task.cancel()
```

**Confidence:** 90% — Proven pattern for mixing WebSocket libraries with FastAPI.

---

### 2. SQLite Async with aiosqlite
**Question:** Best practices for async SQLite in FastAPI with proper connection management?

**Findings:**
- Use `aiosqlite.connect()` with `PRAGMA journal_mode=WAL;` for concurrent reads
- Single connection pool (or single connection for MVP) managed in FastAPI lifespan
- Dependency injection for DB access: `async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]`
- Enable foreign keys: `PRAGMA foreign_keys=ON;`
- Row factory for dict-like access: `conn.row_factory = aiosqlite.Row`

**Schema:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE appointments (
    id TEXT PRIMARY KEY,  -- UUID
    patient_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    date TEXT NOT NULL,   -- YYYY-MM-DD
    time TEXT NOT NULL,   -- HH:MM
    service TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|confirmed|rejected|cancelled|completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_date ON appointments(date);
CREATE INDEX idx_appointments_status ON appointments(status);
```

**Confidence:** 95% — Standard aiosqlite patterns.

---

### 3. JWT Authentication in FastAPI
**Question:** Secure JWT implementation with HttpOnly cookies for MVP?

**Findings:**
- **Library:** `python-jose[cryptography]` for JWT, `passlib[bcrypt]` for password hashing
- **Token:** 8-hour expiry, HS256 algorithm, secret from `JWT_SECRET` env var
- **Cookie:** `HttpOnly=True`, `Secure=False` (dev), `SameSite="lax"`, `max_age=28800`
- **Dependency:** `async def get_current_user(request: Request) -> dict` reads cookie, validates JWT
- **Login endpoint:** `POST /api/v1/auth/login` → sets cookie, returns user info
- **Logout endpoint:** `POST /api/v1/auth/logout` → clears cookie
- **Seed user:** Create default doctor from `DOCTOR_EMAIL`/`DOCTOR_PASSWORD` env vars on startup

**Security notes for MVP:**
- `SameSite="lax"` works for localhost (not `strict`)
- `Secure=False` for HTTP localhost; set `True` in production behind HTTPS
- Rotate `JWT_SECRET` periodically
- Rate limit login endpoint (optional for MVP)

**Confidence:** 95% — Well-established pattern.

---

### 4. AI Receptionist → HTTP API Bridge
**Question:** How to add `create_appointment` function callable from Deepgram function calling?

**Findings:**
- Add new function to `receptionist_functions.py`:
```python
async def create_appointment(
    patient_name: str,
    phone: str,
    date: str,  # YYYY-MM-DD
    time: str,  # HH:MM
    service: str,
    email: str = None
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5000/api/v1/appointments",
            json={...},
            timeout=10.0
        )
        return response.json()
```
- Register in `FUNCTION_MAP` and add to `config.json` functions list
- Function must be `async` since it makes HTTP call
- Return appointment ID for AI confirmation message
- Handle errors gracefully (network, validation, etc.)

**Critical:** The function runs in the existing WebSocket handler context, so `httpx.AsyncClient` works fine.

**Confidence:** 90% — Matches existing function calling pattern.

---

### 5. Pydantic Models for API Validation
**Question:** Request/response models for all 6 endpoints?

**Models:**
```python
# Request
class AppointmentCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(pattern=r'^\+?[\d\s-]{10,}$')
    email: Optional[EmailStr] = None
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(pattern=r'^\d{2}:\d{2}$')
    service: str = Field(min_length=1)

class AppointmentUpdate(BaseModel):
    pass  # No body needed for status transitions

# Response
class AppointmentResponse(BaseModel):
    id: str
    patient_name: str
    phone: str
    email: Optional[str]
    date: str
    time: str
    service: str
    status: Literal["pending", "confirmed", "rejected", "cancelled", "completed"]
    created_at: datetime
    updated_at: datetime

# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
```

**Confidence:** 95% — Standard FastAPI/Pydantic v2.

---

### 6. CORS Configuration
**Question:** CORS settings for frontend served from same origin?

**Findings:**
- Since frontend served via FastAPI `StaticFiles` on same port/origin, CORS not strictly needed
- But for development flexibility (separate dev server), allow:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- `allow_credentials=True` required for HttpOnly cookies

**Confidence:** 90%

---

### 7. Timezone Handling
**Question:** Consistent timezone between AI, DB, and frontend?

**Findings:**
- **Storage:** All timestamps in UTC (SQLite `CURRENT_TIMESTAMP` is UTC)
- **AI/Backend:** Use existing `get_timezone()` from `receptionist_functions.py` for date parsing
- **Frontend:** Receive UTC, display in clinic timezone (from `TIMEZONE` env)
- **API:** Return UTC ISO strings; frontend converts
- **Single source:** `TIMEZONE` env var (e.g., `America/New_York`)

**Confidence:** 90%

---

### 8. Error Handling Patterns
**Question:** Consistent error responses across all endpoints?

**Pattern:**
```python
# Custom exceptions
class AppointmentNotFound(HTTPException):
    def __init__(self, id: str):
        super().__init__(status_code=404, detail=f"Appointment {id} not found")

class InvalidAppointmentData(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

# Global exception handler for consistent format
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )
```

**Confidence:** 95%

---

## Dependencies to Add

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115+ | REST API framework |
| uvicorn[standard] | 0.32+ | ASGI server (already implicit) |
| python-jose[cryptography] | 3.3+ | JWT encoding/decoding |
| passlib[bcrypt] | 1.7+ | Password hashing |
| aiosqlite | 0.20+ | Async SQLite |
| pydantic | 2.10+ | Validation (already in fastapi) |
| httpx | 0.27+ | Async HTTP client for AI bridge |
| python-multipart | 0.0.9+ | Form data parsing for login |

**Add to `pyproject.toml`:**
```toml
dependencies = [
    "python-dotenv>=1.2.2",
    "tzdata>=2026.3",
    "websockets>=17.0.1",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "aiosqlite>=0.20",
    "httpx>=0.27",
    "python-multipart>=0.0.9",
]
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| WebSocket + HTTP conflict | Medium | High | Test voice flow after each change; Option B minimizes changes |
| AI function calling fails | Low | High | Unit test `create_appointment` in isolation with mock server |
| JWT cookie not sent | Medium | Medium | Use `SameSite=lax`, `credentials: include`, test in incognito |
| SQLite locking under polling | Low | Medium | WAL mode, short transactions, single connection OK for MVP |
| Breaking existing voice AI | Low | Critical | Regression test: make test call after every backend change |

---

## Implementation Order (Vertical Slice)

1. **Database** — Schema, connection, lifespan
2. **Auth** — JWT, login/logout, seed user, middleware
3. **Appointments API** — CRUD + status transitions
4. **AI Bridge** — `create_appointment` function + config
5. **Static Files** — Mount `/static` for future frontend
6. **Integration Test** — Voice call → appointment in DB → API returns it

---

## Canonical References

- `.planning/research/STACK.md` — Stack decisions
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow
- `.planning/research/PITFALLS.md` — Critical pitfalls (WebSocket conflict, AI bridge, timezone)
- `.planning/REQUIREMENTS.md` — All 23 phase requirement IDs
- `.planning/ROADMAP.md` — Phase 1 success criteria

---

## The Agent's Discretion (Not Specified)

- Exact project structure for new modules (separate files vs inline in `main.py`)
- Whether to use SQLAlchemy Core vs raw SQL (raw SQL simpler for MVP)
- Exact polling interval default (7s recommended)
- Logging/observability level (minimal for MVP)
- Rate limiting on auth endpoints (optional)

---

*Research completed: 2026-08-16*