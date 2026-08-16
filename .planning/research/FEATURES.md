# Features Research — AI Dental Receptionist Dashboard

**Project:** AI Dental Receptionist — Private Doctor Dashboard MVP
**Context:** Greenfield frontend + brownfield backend extension
**Date:** 2026-08-16

---

## Feature Categories

### Table Stakes (Must Have — Users Expect These)

| Feature | Description | Complexity | Dependencies |
|---------|-------------|------------|--------------|
| Doctor login | Email/password auth with session persistence | Low | Backend auth, SQLite users table |
| Route protection | Redirect unauthenticated users to login | Low | Auth middleware |
| Dashboard overview | Today's count, pending count, confirmed count, upcoming list | Medium | API-01, polling |
| Appointments table | Full list with ID, patient, date, time, service, status | Medium | API-01, polling |
| Status badges | Visual distinction for 5 statuses | Low | Frontend only |
| Confirm action | Pending → Confirmed via API | Medium | API-03, UI feedback |
| Reject action | Pending → Rejected via API | Medium | API-04, UI feedback |
| Cancel action | Confirmed → Cancelled via API | Medium | API-05, UI feedback |
| Complete action | Confirmed → Completed via API | Medium | API-06, UI feedback |
| Patient info display | Name, phone, email, service, date, time | Low | Data model |
| Auto-refresh | Polling every 5-10 seconds | Low | Frontend timer |
| Loading states | Spinners/skeletons for all async ops | Low | Frontend only |
| Error handling | Friendly messages for failures | Low | Frontend + API errors |
| Empty states | "No appointments", "All caught up" | Low | Frontend only |
| Responsive design | Works on mobile/tablet/desktop | Medium | Tailwind CSS |
| Logout | Clear session, redirect to login | Low | Auth |

### Differentiators (Competitive Advantage)

| Feature | Description | Complexity | Notes |
|---------|-------------|------------|-------|
| AI → Dashboard real-time | New bookings appear within 10s without manual refresh | Medium | Polling achieves this |
| Voice-to-dashboard flow | Patient calls → AI books → Doctor sees instantly | High | Core value prop; requires AI-01, AI-02 |
| Medical SaaS aesthetic | Professional dental clinic look (not generic admin) | Medium | Tailwind customization |
| Zero-build frontend | Alpine + Tailwind CDN — no npm, no build step | Low | Unique simplicity |

### Anti-Features (Deliberately NOT Building)

| Feature | Why Excluded |
|---------|--------------|
| Google Calendar sync | Explicitly deferred per requirements |
| OAuth login | Deferred to v2 |
| WhatsApp/SMS | Deferred to v2 |
| Payments | Deferred to v2 |
| Multi-clinic | Deferred to v2 |
| Rescheduling | Explicitly excluded from MVP |
| WebSockets for dashboard | Polling sufficient for MVP |
| Detailed medical records | Deferred to v2 |
| Analytics dashboard | Deferred to v2 |

---

## Feature Dependencies

```
Backend API (Phase 1)
    ├── Auth system
    ├── Appointment CRUD + status transitions
    ├── Data model + SQLite
    └── AI receptionist integration (POST /appointments)

Frontend Core (Phase 2)
    ├── Login page
    ├── Dashboard with polling
    ├── Appointments page with polling
    ├── Status badge components
    ├── Loading/error/empty states
    └── Responsive layout + sidebar

Appointment Actions (Phase 3)
    ├── Confirm button + API call
    ├── Reject button + API call
    ├── Cancel button + API call
    ├── Complete button + API call
    ├── Optimistic UI updates
    └── Button loading/disabled states
```

---

## Complexity Notes

- **Low**: Pure frontend, simple backend endpoints, config changes
- **Medium**: Requires frontend-backend coordination, state management, polling logic
- **High**: Core differentiating flows, cross-system integration

---

## Research Sources

- FastAPI + WebSocket coexistence patterns
- Alpine.js reactivity for polling dashboards
- Medical SaaS design patterns (Linear, Cal.com, medical CRMs)
- JWT session management in FastAPI
- SQLite async patterns with aiosqlite