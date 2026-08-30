import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .service import get_calendar_service
from .db import get_upcoming_appointments, mark_reminder_sent, is_reminder_sent

scheduler = AsyncIOScheduler()


async def check_and_send_reminders():
    """Run every 15 minutes."""
    now = datetime.now()
    
    # 24-hour reminders
    appointments_24h = get_upcoming_appointments(hours_ahead=24)
    for appt in appointments_24h:
        event_id = appt["google_event_id"]
        if not is_reminder_sent(event_id, "24h"):
            appt_time = datetime.fromisoformat(appt["start_time"])
            if appt_time - now <= timedelta(hours=24, minutes=15) and appt_time - now >= timedelta(hours=23, minutes=45):
                print(f"[REMINDER 24h] Would send to {appt['patient_phone']}: {appt['service_name']} at {appt_time}")
                mark_reminder_sent(event_id, "24h")

    # 2-hour reminders
    appointments_2h = get_upcoming_appointments(hours_ahead=2)
    for appt in appointments_2h:
        event_id = appt["google_event_id"]
        if not is_reminder_sent(event_id, "2h"):
            appt_time = datetime.fromisoformat(appt["start_time"])
            if appt_time - now <= timedelta(hours=2, minutes=15) and appt_time - now >= timedelta(hours=1, minutes=45):
                print(f"[REMINDER 2h] Would send to {appt['patient_phone']}: {appt['service_name']} at {appt_time}")
                mark_reminder_sent(event_id, "2h")


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            check_and_send_reminders,
            IntervalTrigger(minutes=15),
            id="reminder_job",
            replace_existing=True,
        )
        scheduler.start()
        print("Reminder scheduler started (every 15 min)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Reminder scheduler stopped")