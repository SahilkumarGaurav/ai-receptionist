import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from .service import get_calendar_service
from .db import save_appointment, init_db

load_dotenv()

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))

SERVICE_DURATION = {
    "cleaning": 60, "checkup": 30, "filling": 45, "crown": 90,
    "root canal": 90, "extraction": 45, "whitening": 60, "consultation": 30,
}


def check_availability(start: datetime, end: datetime) -> bool:
    """Return True if no overlapping events."""
    service = get_calendar_service()
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": CALENDAR_ID}],
    }
    result = service.freebusy().query(body=body).execute()
    busy = result["calendars"][CALENDAR_ID].get("busy", [])
    return len(busy) == 0


def create_appointment(
    patient_name: str,
    service_name: str,
    start_str: str,
    patient_phone: str = None,
    sms_consent: bool = False,
) -> dict:
    """
    Book appointment in Google Calendar.
    Returns: {"success": bool, "event_id": str, "message": str, "start": datetime, "end": datetime}
    """
    init_db()

    service_name_lower = service_name.lower().strip()
    duration = SERVICE_DURATION.get(service_name_lower, 60)

    try:
        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)
    except ValueError:
        return {"success": False, "message": "Invalid start format. Use 'YYYY-MM-DD HH:MM'"}

    end = start + timedelta(minutes=duration)

    if not check_availability(start, end):
        return {"success": False, "message": "Time slot not available"}

    service = get_calendar_service()

    event = {
        "summary": f"Plumbing: {service_name.title()} - {patient_name}",
        "description": (
            f"Customer: {patient_name}\n"
            f"Service: {service_name.title()} ({duration}min)\n"
            f"Phone: {patient_phone or 'N/A'}\n"
            f"SMS Consent: {sms_consent}"
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": str(TIMEZONE)},
        "end": {"dateTime": end.isoformat(), "timeZone": str(TIMEZONE)},
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": 30}]
        },
        "extendedProperties": {
            "private": {
                "patient_name": patient_name,
                "patient_phone": patient_phone or "",
                "service_name": service_name_lower,
                "sms_consent": str(sms_consent).lower(),
            }
        },
    }

    created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    event_id = created["id"]

    save_appointment(patient_name, patient_phone, event_id, service_name_lower, start.isoformat(), end.isoformat(), sms_consent)

    return {
        "success": True,
        "event_id": event_id,
        "message": f"Booked {service_name.title()} for {patient_name} on {start.strftime('%b %d at %I:%M %p')}",
        "start": start,
        "end": end,
    }


def cancel_appointment(event_id: str) -> dict:
    service = get_calendar_service()
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        return {"success": True, "message": "Appointment cancelled"}
    except Exception as e:
        return {"success": False, "message": str(e)}