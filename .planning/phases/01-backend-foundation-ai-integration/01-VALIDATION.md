---
phase: 1
slug: backend-foundation-ai-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pytest.ini` (Wave 0 creates) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | MODEL-01..10 | T-01-01 | SQL injection prevention via parameterized queries | unit | `uv run pytest tests/test_db.py -k "schema"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | MODEL-01..10 | — | WAL mode enabled, foreign keys on | unit | `uv run pytest tests/test_db.py -k "pragma"` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | AUTH-01..05 | T-01-02 | Passwords bcrypt-hashed, JWT HS256, HttpOnly cookie | unit | `uv run pytest tests/test_auth.py -k "login"` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | SEC-01..05 | T-01-03 | Cookie SameSite=lax, Secure=False (dev), rotation | unit | `uv run pytest tests/test_auth.py -k "cookie"` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | API-01..10 | T-01-04 | Input validation via Pydantic, 400 on invalid | unit | `uv run pytest tests/test_api.py -k "validate"` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 1 | API-01..10 | — | 404 on not found, 401 on unauth | unit | `uv run pytest tests/test_api.py -k "status"` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 1 | AI-01, AI-03 | T-01-05 | create_appointment calls API, returns ID | unit | `uv run pytest tests/test_ai_bridge.py` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 1 | — | — | FastAPI + WebSocket both serve on :5000 | integration | `uv run pytest tests/test_integration.py -k "ws_and_http"` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 1 | — | — | Existing voice flow unbroken | manual | Make test call via Twilio/Deepgram | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pytest.ini` — configure asyncio mode, test paths
- [ ] `tests/conftest.py` — shared fixtures: `app`, `client`, `db`, `auth_headers`
- [ ] `tests/test_db.py` — schema creation, WAL mode, CRUD
- [ ] `tests/test_auth.py` — login, logout, cookie, JWT validation
- [ ] `tests/test_api.py` — all 6 endpoints, validation, status codes
- [ ] `tests/test_ai_bridge.py` — create_appointment function
- [ ] `tests/test_integration.py` — WebSocket + HTTP coexistence
- [ ] `uv add --dev pytest pytest-asyncio httpx` — if not present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Voice AI creates appointment end-to-end | AI-01, AI-03 | Requires Deepgram/Twilio credentials | 1. Start server 2. Call Twilio number 3. Speak to AI 4. Verify appointment in DB |
| Dashboard polling sees new appointment | AI-02 | Requires frontend (Phase 2) | Deferred to Phase 2 validation |
| JWT cookie works in browser | SEC-03 | Browser cookie behavior | 1. Login via UI 2. Check DevTools Application → Cookies 3. Verify HttpOnly, SameSite=lax |
| Mobile responsive layout | UI-03 | Visual verification | Deferred to Phase 2 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---

## Threat Model (ASVS Level 1)

| ID | Threat | Severity | Mitigation |
|----|--------|----------|------------|
| T-01-01 | SQL Injection via appointment fields | High | Parameterized queries only; Pydantic validation |
| T-01-02 | Weak password storage | High | bcrypt with cost factor 12 |
| T-01-03 | JWT token theft via XSS | Medium | HttpOnly + SameSite=lax cookies |
| T-01-04 | Unauthorized API access | High | Auth dependency on all endpoints |
| T-01-05 | AI function call spoofing | Medium | Internal network only; no public exposure |