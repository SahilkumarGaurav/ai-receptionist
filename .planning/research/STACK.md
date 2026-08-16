# Stack Research — AI Dental Receptionist Dashboard

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Context:** Greenfield frontend + brownfield backend extension
**Date:** 2026-08-16

---

## Recommended Stack

### Backend (Extend Existing)

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| Language | Python | 3.14 | Already in use; matches existing `main.py` |
| Web Framework | FastAPI | 0.115+ | Add REST API to existing WebSocket server; async-native; auto OpenAPI docs |
| ASGI Server | Uvicorn | 0.32+ | Runs both WebSocket (Deepgram) and HTTP (API) |
| Auth | python-jose + passlib | Latest | JWT tokens + bcrypt; simple, replaceable later |
| Data Store | SQLite + aiosqlite | Built-in + 0.20+ | Zero-config for MVP; migratable to PostgreSQL |
| Validation | Pydantic | 2.10+ | Request/response models; integrates with FastAPI |
| CORS | fastapi.middleware.cors | Built-in | Dashboard frontend on different port |
| Env Config | python-dotenv | 1.2+ | Already in use |

### Frontend

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| Framework | Alpine.js | 3.14+ | Lightweight (15KB), no build step, works with static files served by FastAPI |
| Alternative | Vue 3 (CDN) | 3.5+ | If more reactivity needed; still no build step via CDN |
| Styling | Tailwind CSS (CDN) | 3.4+ | Utility-first, medical SaaS look achievable, no build |
| Icons | Lucide (CDN) | Latest | Clean medical icons |
| Date/Time | dayjs (CDN) | 1.11+ | Lightweight date formatting |
| HTTP Client | Native fetch | — | No dependency needed |

### What NOT to Use

| Technology | Why Not |
|------------|---------|
| React/Next.js | Overkill for MVP; requires build step, Node.js, adds complexity |
| Django/Flask | FastAPI better for async + WebSocket coexistence |
| PostgreSQL | Overkill for MVP; SQLite sufficient, easy migration later |
| WebSockets for dashboard | Polling simpler; existing WS used for voice only |
| Firebase/Supabase auth | Deferred to v2; simple JWT session works for MVP |
| Redis | Not needed for MVP polling architecture |
| Celery/Background tasks | Not needed for MVP |

---

## Confidence Levels

| Recommendation | Confidence | Notes |
|----------------|------------|-------|
| FastAPI + Uvicorn | 95% | Proven pattern for adding HTTP to existing WS server |
| SQLite + aiosqlite | 90% | Standard Python, zero config |
| Alpine.js + Tailwind CDN | 85% | Works but less common than Vue/React; verify reactivity needs |
| JWT + bcrypt | 95% | Industry standard, replaceable |
| Polling (5-10s) | 90% | Meets MVP requirement; WebSocket can be added later |

---

## Implementation Notes

1. **Single Uvicorn process**: Run both WebSocket handler (existing) and FastAPI routes in same event loop
2. **Static files**: Serve frontend from `/static` via FastAPI `StaticFiles`
3. **API prefix**: All endpoints under `/api/v1` for versioning
4. **Auth middleware**: Dependency injection for protected routes
5. **Database**: Single `appointments.db` file in project root