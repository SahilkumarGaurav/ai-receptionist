# Requirements: AI Dental Receptionist — Private Doctor Dashboard MVP

**Defined:** 2026-08-16
**Core Value:** Dentists can instantly see and manage every appointment booked by the AI receptionist without leaving their chair — no manual entry, no missed bookings, no double-booking.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [ ] **AUTH-01**: Doctor can log in at `/login` with email/password
- [ ] **AUTH-02**: Doctor session persists across browser refresh
- [ ] **AUTH-03**: Doctor can log out from any page
- [ ] **AUTH-04**: Unauthenticated users are redirected to `/login` when accessing `/dashboard` or `/appointments`
- [ ] **AUTH-05**: Session expires after configurable timeout (default 8 hours)

### Dashboard Overview

- [ ] **DASH-01**: Dashboard displays count of today's appointments
- [ ] **DASH-02**: Dashboard displays count of pending appointments awaiting confirmation
- [ ] **DASH-03**: Dashboard displays count of confirmed appointments
- [ ] **DASH-04**: Dashboard shows table of upcoming appointments with patient name, date, time, service, status
- [ ] **DASH-05**: Dashboard auto-refreshes appointment data every 5-10 seconds via polling
- [ ] **DASH-06**: Dashboard shows loading state while fetching data
- [ ] **DASH-07**: Dashboard shows friendly error message if backend unavailable
- [ ] **DASH-08**: Dashboard shows "No appointments yet" when empty
- [ ] **DASH-09**: Dashboard shows "You're all caught up" when no pending appointments

### Appointments Management

- [ ] **APPT-01**: Appointments page at `/appointments` displays all appointments in a table
- [ ] **APPT-02**: Table shows: Appointment ID, Patient Name, Date, Time, Dental Service, Status
- [ ] **APPT-03**: Status badges are visually distinct: Pending (yellow), Confirmed (green), Rejected (red), Cancelled (gray), Completed (blue)
- [ ] **APPT-04**: Appointments page auto-refreshes every 5-10 seconds via polling
- [ ] **APPT-05**: Appointments page shows loading state while fetching
- [ ] **APPT-06**: Appointments page shows error state on failure
- [ ] **APPT-07**: Appointments page shows empty state when no appointments exist

### Appointment Actions

- [ ] **ACTN-01**: Doctor can click "Confirm" on pending appointment → status changes to confirmed
- [ ] **ACTN-02**: Doctor can click "Reject" on pending appointment → status changes to rejected
- [ ] **ACTN-03**: Doctor can click "Cancel" on confirmed appointment → status changes to cancelled
- [ ] **ACTN-04**: Doctor can click "Complete" on confirmed appointment → status changes to completed
- [ ] **ACTN-05**: Action buttons show loading state while processing
- [ ] **ACTN-06**: Action buttons are disabled during processing to prevent double-clicks
- [ ] **ACTN-07**: UI updates immediately after successful action (optimistic or refetch)
- [ ] **ACTN-08**: Friendly error message shown if action fails

### Patient Information

- [ ] **PAT-01**: Appointment displays patient name
- [ ] **PAT-02**: Appointment displays patient phone number
- [ ] **PAT-03**: Appointment displays patient email (if available)
- [ ] **PAT-04**: Appointment displays requested dental service
- [ ] **PAT-05**: Appointment displays date and time

### Backend API

- [ ] **API-01**: `GET /api/appointments` returns all appointments as JSON array
- [ ] **API-02**: `POST /api/appointments` creates new appointment from AI receptionist
- [ ] **API-03**: `PATCH /api/appointments/{id}/confirm` changes status to confirmed
- [ ] **API-04**: `PATCH /api/appointments/{id}/reject` changes status to rejected
- [ ] **API-05**: `PATCH /api/appointments/{id}/cancel` changes status to cancelled
- [ ] **API-06**: `PATCH /api/appointments/{id}/complete` changes status to completed
- [ ] **API-07**: API validates request payloads and returns 400 for invalid data
- [ ] **API-08**: API returns 404 for appointment not found
- [ ] **API-09**: API returns 401 for unauthenticated requests (if auth added to API)
- [ ] **API-10**: API does not expose secrets, API keys, or .env values

### Appointment Data Model

- [ ] **MODEL-01**: Appointment has unique ID (string/UUID)
- [ ] **MODEL-02**: Appointment has patient_name (string)
- [ ] **MODEL-03**: Appointment has phone (string)
- [ ] **MODEL-04**: Appointment has email (string, optional)
- [ ] **MODEL-05**: Appointment has date (YYYY-MM-DD)
- [ ] **MODEL-06**: Appointment has time (HH:MM)
- [ ] **MODEL-07**: Appointment has service (string from predefined list)
- [ ] **MODEL-08**: Appointment has status (pending|confirmed|rejected|cancelled|completed)
- [ ] **MODEL-09**: Appointment has created_at timestamp
- [ ] **MODEL-10**: Service values supported: Dental Cleaning, Dental Consultation, Tooth Extraction, Root Canal, Dental Filling, Teeth Whitening, Braces Consultation

### AI Receptionist Integration

- [ ] **AI-01**: AI receptionist can create appointment via `POST /api/appointments` after collecting patient info
- [ ] **AI-02**: New appointment appears in dashboard within 10 seconds (polling interval)
- [ ] **AI-03**: Appointment created by AI has status "pending" by default

### UI/UX

- [ ] **UI-01**: Clean, professional medical SaaS design (not generic admin template)
- [ ] **UI-02**: Simple sidebar with Dashboard, Appointments, Patients, Settings, Logout
- [ ] **UI-03**: Responsive design works on desktop, laptop, tablet, mobile
- [ ] **UI-04**: Clear typography, spacious layout, rounded cards
- [ ] **UI-05**: Subtle animations only, no unnecessary visual effects
- [ ] **UI-06**: Professional appointment table with sortable columns (optional)
- [ ] **UI-07**: Clear Confirm/Reject/Cancel/Complete buttons with distinct styling

### Security

- [ ] **SEC-01**: Dashboard routes require authentication
- [ ] **SEC-02**: API endpoints validate requests
- [ ] **SEC-03**: No API keys or secrets in frontend code
- [ ] **SEC-04**: No .env values exposed to frontend
- [ ] **SEC-05**: Single doctor data isolation (no cross-access)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Authentication

- **AUTH-06**: Firebase/Supabase authentication integration
- **AUTH-07**: Password reset via email
- **AUTH-08**: Two-factor authentication (2FA)

### Calendar & Notifications

- **CAL-01**: Google Calendar sync for confirmed appointments
- **NOTIF-01**: WhatsApp/SMS confirmation to patients
- **NOTIF-02**: Email confirmation to patients
- **NOTIF-03**: Doctor notification for new pending appointments

### Advanced Features

- **ADV-01**: Appointment rescheduling (drag-drop or modal)
- **ADV-02**: Patient medical records / dental charts
- **ADV-03**: X-ray / document storage
- **ADV-04**: Multi-clinic / multi-doctor support
- **ADV-05**: Staff permissions (receptionist, hygienist, admin)
- **ADV-06**: Analytics dashboard (booking trends, no-show rates, revenue)
- **ADV-07**: AI call recordings playback
- **ADV-08**: Payments / billing integration
- **ADV-09**: Subscription / SaaS billing

### Infrastructure

- **INFRA-01**: WebSocket real-time updates (replace polling)
- **INFRA-02**: PostgreSQL / production database
- **INFRA-03**: Docker containerization
- **INFRA-04**: CI/CD pipeline

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Google Calendar | Explicitly deferred per requirements |
| Google OAuth | Deferred to v2 |
| WhatsApp/SMS | Deferred to v2 |
| Payments | Deferred to v2 |
| Subscription system | Deferred to v2 |
| Advanced analytics | Deferred to v2 |
| Detailed medical records | Deferred to v2 |
| Dental charts | Deferred to v2 |
| X-ray storage | Deferred to v2 |
| Multi-clinic management | Deferred to v2 |
| Complex staff permissions | Deferred to v2 |
| AI call recordings | Deferred to v2 |
| Advanced notifications | Deferred to v2 |
| WebSockets | Polling acceptable for MVP |
| Appointment rescheduling | Explicitly excluded from MVP |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
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
| ACTN-01 | Phase 3 | Pending |
| ACTN-02 | Phase 3 | Pending |
| ACTN-03 | Phase 3 | Pending |
| ACTN-04 | Phase 3 | Pending |
| ACTN-05 | Phase 3 | Pending |
| ACTN-06 | Phase 3 | Pending |
| ACTN-07 | Phase 3 | Pending |
| ACTN-08 | Phase 3 | Pending |
| PAT-01 | Phase 2 | Pending |
| PAT-02 | Phase 2 | Pending |
| PAT-03 | Phase 2 | Pending |
| PAT-04 | Phase 2 | Pending |
| PAT-05 | Phase 2 | Pending |
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
| AI-02 | Phase 2 | Pending |
| AI-03 | Phase 1 | Pending |
| UI-01 | Phase 2 | Pending |
| UI-02 | Phase 2 | Pending |
| UI-03 | Phase 2 | Pending |
| UI-04 | Phase 2 | Pending |
| UI-05 | Phase 2 | Pending |
| UI-06 | Phase 2 | Pending |
| UI-07 | Phase 2 | Pending |
| SEC-01 | Phase 1 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 1 | Pending |
| SEC-04 | Phase 1 | Pending |
| SEC-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 52 total
- Mapped to phases: 52
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-16*
*Last updated: 2026-08-16 after initial definition*