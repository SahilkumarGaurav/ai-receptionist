# Roadmap: AI Dental Receptionist — Private Doctor Dashboard MVP

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Mode:** MVP (Vertical slices — each phase delivers end-to-end user capability)
**Generated:** 2026-08-16
**Requirements:** 52 v1 requirements mapped across 3 phases

---

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Backend Foundation & AI Integration | Extend `main.py` with FastAPI, SQLite, Auth, and appointment CRUD; connect AI receptionist to create appointments | 23 (AUTH-01–05, API-01–10, MODEL-01–10, AI-01, AI-03, SEC-01–05) | 1. Voice AI creates appointment visible in DB<br>2. All API endpoints return correct responses<br>3. Login works with JWT cookie<br>4. Existing voice flow unbroken |
| 2 | Frontend Core — Dashboard & Appointments | Build login, dashboard, appointments pages with polling, loading/error/empty states, responsive medical SaaS UI | 23 (DASH-01–09, APPT-01–07, PAT-01–05, UI-01–07, AI-02) | 1. Doctor logs in, sees dashboard with live data<br>2. Appointments page shows full table with badges<br>3. Polling updates new bookings within 10s<br>4. Works on mobile/tablet/desktop<br>5. Loading/error/empty states display correctly |
| 3 | Appointment Actions — Confirm, Reject, Cancel, Complete | Doctor can transition appointment status via UI; immediate feedback; backend sync | 6 (ACTN-01–08) | 1. Confirm changes pending→confirmed (green badge)<br>2. Reject changes pending→rejected (red badge)<br>3. Cancel changes confirmed→cancelled (gray badge)<br>4. Complete changes confirmed→completed (blue badge)<br>5. Buttons disabled during processing<br>6. Errors shown friendlily |

---

## Phase 1: Backend Foundation & AI Integration

**Goal:** Extend `main.py` with FastAPI REST API, SQLite database, JWT authentication, and connect AI receptionist to create appointments.

**Mode:** mvp

**Success Criteria:**
1. Voice AI creates appointment → visible in SQLite DB within 1 second
2. All 6 API endpoints (`GET`, `POST`, 4×`PATCH`) return correct JSON responses
3. Doctor can log in at `/login` → receives HttpOnly JWT cookie → accesses `/dashboard`
4. Existing Deepgram/Twilio voice flow works identically after changes

**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, API-09, API-10, MODEL-01, MODEL-02, MODEL-03, MODEL-04, MODEL-05, MODEL-06, MODEL-07, MODEL-08, MODEL-09, MODEL-10, AI-01, AI-03, SEC-01, SEC-02, SEC-03, SEC-04, SEC-05

**Tasks:**

1. **Database Schema & Models**
   - Create `appointments.db` with `appointments` and `users` tables
   - Enable WAL mode for concurrency
   - Pydantic models for request/response validation

2. **FastAPI App + Uvicorn Integration**
   - Add FastAPI instance to `main.py`
   - Mount static files at `/static`
   - Lifespan manager for DB connection + existing WebSocket server
   - CORS middleware for frontend origin

3. **Authentication System**
   - `POST /api/v1/auth/login` — email/password → sets HttpOnly JWT cookie
   - `POST /api/v1/auth/logout` — clears cookie
   - `GET /api/v1/auth/me` — validates cookie, returns user
   - JWT: 8-hour expiry, bcrypt password hash, `SameSite=Lax`
   - Seed default doctor user (email from `.env`, password from `.env`)

4. **Appointment CRUD API**
   - `GET /api/v1/appointments` — list all, optional `?status=` filter
   - `POST /api/v1/appointments` — create (AI receptionist), defaults status=pending
   - `PATCH /api/v1/appointments/{id}/confirm` — status=confirmed
   - `PATCH /api/v1/appointments/{id}/reject` — status=rejected
   - `PATCH /api/v1/appointments/{id}/cancel` — status=cancelled
   - `PATCH /api/v1/appointments/{id}/complete` — status=completed
   - All: 404 if not found, 400 if invalid, 401 if unauthenticated

5. **AI Receptionist Integration**
   - Add `create_appointment` function to `receptionist_functions.py`
   - Function calls `POST /api/v1/appointments` via `httpx.AsyncClient`
   - Register in `FUNCTION_MAP` and `config.json` functions list
   - Returns appointment ID for AI confirmation message

6. **Dependencies & Config**
   - Update `pyproject.toml`: fastapi, uvicorn, python-jose, passlib, aiosqlite, pydantic, httpx
   - Add `JWT_SECRET`, `DOCTOR_EMAIL`, `DOCTOR_PASSWORD` to `.env`
   - Run `uv sync`

**Validation:**
- `curl` all endpoints with valid/invalid data
- Make test call to AI receptionist → verify appointment in DB
- Verify existing voice flow still works (Deepgram connection, function calling)

---

## Phase 2: Frontend Core — Dashboard & Appointments

**Goal:** Build complete frontend with login, dashboard overview, appointments management, polling, and professional medical SaaS UI.

**Mode:** mvp

**Success Criteria:**
1. Doctor navigates to `/` → redirects to `/login` → enters credentials → lands on `/dashboard`
2. Dashboard shows: today's count, pending count, confirmed count, upcoming table (5 rows)
3. Appointments page at `/appointments` shows full table with all columns + status badges
4. New AI booking appears in dashboard within 10 seconds (polling)
5. Responsive: usable on mobile (375px), tablet (768px), desktop (1440px)
6. Loading skeletons, error banners, empty states all display appropriately

**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07, DASH-08, DASH-09, APPT-01, APPT-02, APPT-03, APPT-04, APPT-05, APPT-06, APPT-07, PAT-01, PAT-02, PAT-03, PAT-04, PAT-05, UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, AI-02

**Tasks:**

1. **Frontend Structure**
   - `static/index.html` — entry point, loads Alpine.js + Tailwind CDN
   - `static/app.js` — Alpine.js components, API client, polling logic
   - `static/styles.css` — custom medical SaaS tweaks (minimal)
   - Routes: `/login`, `/dashboard`, `/appointments` (SPA-style with Alpine)

2. **Authentication Flow**
   - Login page: email/password form, validation, submit to API
   - On success: store token in memory, redirect to `/dashboard`
   - Route guard: check auth on protected routes, redirect to `/login`
   - Logout button in sidebar → calls API → clears state → redirects

3. **Layout & Navigation**
   - Sidebar: Dashboard, Appointments, Patients (disabled), Settings (disabled), Logout
   - Mobile: hamburger menu, collapsible sidebar
   - Header: clinic name, current date, doctor name
   - Medical SaaS color palette: teal/blue primary, neutral grays, semantic status colors

4. **Dashboard Page**
   - Stats cards: Today's Appointments, Pending, Confirmed (large numbers, icons)
   - Upcoming table: Patient, Date, Time, Service, Status (badge)
   - Polling: `setInterval` every 7 seconds, `fetch` with `credentials: 'include'`
   - Loading: skeleton cards on initial load
   - Error: dismissible banner "Unable to connect to receptionist server"
   - Empty: "No appointments yet" illustration + message

5. **Appointments Page**
   - Full table: ID, Patient, Date, Time, Service, Status, Actions (for pending/confirmed)
   - Sortable columns (Alpine.js sort)
   - Status badges: Pending (amber), Confirmed (emerald), Rejected (red), Cancelled (gray), Completed (blue)
   - Same polling, loading, error, empty states as dashboard
   - Pagination (client-side) if >20 rows

6. **Patient Info Display**
   - Click row → modal/drawer with: Name, Phone, Email, Service, Date, Time, Status, Created At
   - Accessible from both dashboard upcoming table and appointments table

7. **Polish & Responsive**
   - Tailwind responsive utilities: `grid-cols-1 md:grid-cols-3`, `hidden md:block`, `overflow-x-auto` tables
   - Touch targets ≥44px on mobile
   - Focus rings, ARIA labels
   - Subtle transitions: badge color change, card hover, modal fade

**Validation:**
- Open in Chrome DevTools device toolbar: iPhone SE, iPad, Desktop
- Test polling: create appointment via API → verify appears in <10s
- Test auth: logout → try `/dashboard` → redirects to login
- Test error: stop backend → verify error banner
- Test empty: clear DB → verify empty states

---

## Phase 3: Appointment Actions — Confirm, Reject, Cancel, Complete

**Goal:** Enable doctor to transition appointment statuses with immediate UI feedback and backend synchronization.

**Mode:** mvp

**Success Criteria:**
1. Pending appointment: "Confirm" button → status=confirmed (green badge) → API called
2. Pending appointment: "Reject" button → status=rejected (red badge) → API called
3. Confirmed appointment: "Cancel" button → status=cancelled (gray badge) → API called
4. Confirmed appointment: "Complete" button → status=completed (blue badge) → API called
5. Buttons show spinner, disabled during request, re-enabled on success/error
6. Error: friendly toast "Failed to update appointment. Please try again."

**Requirements:** ACTN-01, ACTN-02, ACTN-03, ACTN-04, ACTN-05, ACTN-06, ACTN-07, ACTN-08

**Tasks:**

1. **Action Buttons in Tables**
   - Pending row: [Confirm] [Reject] (teal + red)
   - Confirmed row: [Cancel] [Complete] (gray + blue)
   - Other statuses: no actions (or "View" only)
   - Buttons use `<button type="button">` with Alpine `@click`

2. **Optimistic UI Updates**
   - On click: immediately update local status, show spinner on button
   - `fetch` PATCH to appropriate endpoint
   - On success: keep optimistic state, remove spinner
   - On error: revert local status, show error toast, re-enable button

3. **Error Handling & Feedback**
   - Toast notification system (Alpine.js store)
   - Success: "Appointment confirmed" (auto-dismiss 3s)
   - Error: "Failed to confirm appointment. Please try again." (dismissible)
   - Network error: "Connection lost. Retrying..." with exponential backoff

4. **Polling Sync**
   - After any action, next poll (≤7s) reconciles state
   - Or: manual `fetch` after success for instant sync across tabs

5. **Accessibility**
   - Buttons: `aria-label="Confirm appointment for Rahul Sharma"`
   - Loading: `aria-busy="true"` on button
   - Toasts: `role="alert"`, `aria-live="polite"`

**Validation:**
- Test each action: confirm, reject, cancel, complete
- Verify badge color changes instantly
- Verify API called with correct endpoint
- Test error: disconnect network → click → verify toast + revert
- Test double-click prevention: rapid clicks → only one request
- Test multi-tab: action in tab A → tab B updates on next poll

---

## Traceability Matrix

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| API-01 | Phase 1 | Pending |
| API-02 | Phase 1 | Pending |
| API-03 | Phase 1 | Pending |
| API-04 | Phase 1 | Pending |
| API-05 | Phase 1 | Pending |
| API-06 | Phase 1 | Pending |
| API-07 | Phase 1 | Pending |
| API-08 | Phase 1 | Pending |
| API-09 | Phase 1 | Pending |
| API-10 | Phase 1 | Pending |
| MODEL-01 | Phase 1 | Pending |
| MODEL-02 | Phase 1 | Pending |
| MODEL-03 | Phase 1 | Pending |
| MODEL-04 | Phase 1 | Pending |
| MODEL-05 | Phase 1 | Pending |
| MODEL-06 | Phase 1 | Pending |
| MODEL-07 | Phase 1 | Pending |
| MODEL-08 | Phase 1 | Pending |
| MODEL-09 | Phase 1 | Pending |
| MODEL-10 | Phase 1 | Pending |
| AI-01 | Phase 1 | Pending |
| AI-03 | Phase 1 | Pending |
| SEC-01 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 1 | Pending |
| SEC-04 | Phase 1 | Pending |
| SEC-05 | Phase 1 | Pending |
| DASH-01 | Phase 2 | Pending |
| DASH-02 | Phase 2 | Pending |
| DASH-03 | Phase 2 | Pending |
| DASH-04 | Phase 2 | Pending |
| DASH-05 | Phase 2 | Pending |
| DASH-06 | Phase 2 | Pending |
| DASH-07 | Phase 2 | Pending |
| DASH-08 | Phase 2 | Pending |
| DASH-09 | Phase 2 | Pending |
| APPT-01 | Phase 2 | Pending |
| APPT-02 | Phase 2 | Pending |
| APPT-03 | Phase 2 | Pending |
| APPT-04 | Phase 2 | Pending |
| APPT-05 | Phase 2 | Pending |
| APPT-06 | Phase 2 | Pending |
| APPT-07 | Phase 2 | Pending |
| PAT-01 | Phase 2 | Pending |
| PAT-02 | Phase 2 | Pending |
| PAT-03 | Phase 2 | Pending |
| PAT-04 | Phase 2 | Pending |
| PAT-05 | Phase 2 | Pending |
| UI-01 | Phase 2 | Pending |
| UI-02 | Phase 2 | Pending |
| UI-03 | Phase 2 | Pending |
| UI-04 | Phase 2 | Pending |
| UI-05 | Phase 2 | Pending |
| UI-06 | Phase 2 | Pending |
| UI-07 | Phase 2 | Pending |
| AI-02 | Phase 2 | Pending |
| ACTN-01 | Phase 3 | Pending |
| ACTN-02 | Phase 3 | Pending |
| ACTN-03 | Phase 3 | Pending |
| ACTN-04 | Phase 3 | Pending |
| ACTN-05 | Phase 3 | Pending |
| ACTN-06 | Phase 3 | Pending |
| ACTN-07 | Phase 3 | Pending |
| ACTN-08 | Phase 3 | Pending |

**Coverage:** 52/52 v1 requirements mapped ✓

---

## Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FastAPI + WebSocket conflict | Medium | High | Test early in Phase 1 Task 2; fallback: separate ports |
| AI function calling fails | Low | High | Unit test `create_appointment` function in isolation |
| Polling too aggressive | Low | Medium | Configurable interval (env var); start at 7s |
| JWT cookie issues on localhost | Medium | Medium | Use `SameSite=Lax`, test in incognito |
| Mobile table usability | Medium | Medium | Card layout on <640px; horizontal scroll fallback |
| Breaking existing voice AI | Low | Critical | Regression test after each Phase 1 task |

---

## Next Steps

After Phase 1 complete: Run `/gsd-plan-phase 2` to detail frontend tasks.
After Phase 2 complete: Run `/gsd-plan-phase 3` to detail action tasks.

---

*Roadmap created: 2026-08-16*
*Last updated: 2026-08-16 after initial creation*