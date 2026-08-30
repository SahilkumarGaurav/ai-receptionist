import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from gcal.book_appointment import create_appointment, cancel_appointment


# ------------------------------------------------------------
# Timezone helper
# ------------------------------------------------------------

def get_timezone():
    tz_name = os.getenv("TIMEZONE", "UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


# ------------------------------------------------------------
# Plumbing services
# Booking only. No pricing yet.
# ------------------------------------------------------------

SERVICES_DB = {
    "leak repair": {"duration": 60},
    "clogged drain": {"duration": 45},
    "toilet repair": {"duration": 45},
    "water heater": {"duration": 90},
    "faucet repair": {"duration": 30},
    "sink repair": {"duration": 45},
    "sewer service": {"duration": 120},
    "pipe repair": {"duration": 90},
    "pipe replacement": {"duration": 120},
    "water pressure": {"duration": 45},
    "no hot water": {"duration": 60},
    "installation": {"duration": 60},
    "inspection": {"duration": 45},
    "emergency plumbing": {"duration": 60},
    "general plumbing": {"duration": 60},
}


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def parse_12hr_time(time_str: str) -> str:
    """
    Convert 12-hour format (e.g., '2:30 PM', '11:00 AM') to 24-hour format (e.g., '14:30', '11:00').
    """
    import re
    time_str = time_str.strip().upper()
    
    # Match patterns like "2:30 PM", "2:30PM", "11:00 AM", "11 AM", etc.
    match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$', time_str)
    if not match:
        # If already in 24-hour format, return as-is
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            return time_str  # Let downstream handle the error
    
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)
    
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    return f"{hour:02d}:{minute:02d}"


def resolve_relative_date(relative_date: str) -> str:
    """
    Convert relative date expressions to YYYY-MM-DD format.
    Handles: today, tomorrow, day after tomorrow, next monday, next tuesday, etc.
    Also handles: this monday, this tuesday, etc.
    """
    import re
    from datetime import datetime, timedelta
    
    tz = get_timezone()
    today = datetime.now(tz).date()
    
    expr = relative_date.strip().lower()
    
    # Direct matches
    if expr in ("today", "now"):
        return today.strftime("%Y-%m-%d")
    
    if expr in ("tomorrow", "tom"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if expr in ("day after tomorrow", "in two days"):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Day names
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    # "this <day>" - this week's occurrence (including today)
    this_day_match = re.match(r"^this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", expr)
    if this_day_match:
        target_weekday = weekdays[this_day_match.group(1)]
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # "next <day>" - next week's occurrence
    next_day_match = re.match(r"^next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", expr)
    if next_day_match:
        target_weekday = weekdays[next_day_match.group(1)]
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # "<day>" alone - assume this week (or next if already passed)
    if expr in weekdays:
        target_weekday = weekdays[expr]
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0:
            days_ahead = 7  # If today, assume next week
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # "in X days"
    in_days_match = re.match(r"^in\s+(\d+)\s*days?$", expr)
    if in_days_match:
        days = int(in_days_match.group(1))
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # "X days from now"
    days_from_match = re.match(r"^(\d+)\s*days?\s+from\s+now$", expr)
    if days_from_match:
        days = int(days_from_match.group(1))
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Already in YYYY-MM-DD format
    try:
        datetime.strptime(expr, "%Y-%m-%d")
        return expr
    except ValueError:
        pass
    
    # Default to today if unrecognized
    return today.strftime("%Y-%m-%d")


# ------------------------------------------------------------
# Function 1: lookup_customer
# Placeholder for now.
# Later you can connect this to your real customer database.
# ------------------------------------------------------------

def lookup_customer(customer_name: str = None, phone: str = None):
    """
    Look up customer information.
    Currently returns placeholder data so the AI does not crash.
    """
    if customer_name:
        return {
            "found": True,
            "customer_name": customer_name,
            "phone": phone,
            "status": "Active",
            "message": "Customer record found."
        }
    
    return {
        "found": False,
        "message": "No customer information was provided."
    }


def book_appointment(
    customer_name: str,
    phone: str,
    service_address: str,
    preferred_date: str,
    preferred_time: str,
    service_type: str,
    problem_description: str,
    urgency: str,
    customer_email: str = None,
) -> dict:
    """
    Wrapper that maps config parameters to create_appointment.
    Returns JSON-serializable dict (datetime converted to ISO strings).
    Sends confirmation email for non-emergency bookings if email provided.
    """
    # Resolve relative date (tomorrow, next monday, etc.)
    resolved_date = resolve_relative_date(preferred_date)
    
    # Convert 12-hour format to 24-hour format
    time_24hr = parse_12hr_time(preferred_time)
    
    # Combine date and time into start_str format
    start_str = f"{resolved_date} {time_24hr}"
    
    # Map service_type to service_name (they're the same in our case)
    service_name = service_type.lower().strip()
    
    # Call the actual booking function
    result = create_appointment(
        patient_name=customer_name,
        service_name=service_name,
        start_str=start_str,
        patient_phone=phone,
        sms_consent=False,
    )
    
    # Convert datetime objects to ISO strings for JSON serialization
    if result.get("success") and isinstance(result.get("start"), datetime):
        result["start"] = result["start"].isoformat()
    if result.get("success") and isinstance(result.get("end"), datetime):
        result["end"] = result["end"].isoformat()
    
    # Add plumbing-specific info to result
    if result.get("success"):
        result["customer_name"] = customer_name
        result["phone"] = phone
        result["service_address"] = service_address
        result["service_type"] = service_type
        result["problem_description"] = problem_description
        result["urgency"] = urgency
        
        # Save/update customer in dashboard database
        try:
            import sqlite3
            from datetime import datetime
            from zoneinfo import ZoneInfo
            import os
            DB_PATH = "calendar.db"
            TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/New_York"))
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO customers (name, phone, email, address, last_contact)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(name, phone) DO UPDATE SET
                        email = COALESCE(excluded.email, customers.email),
                        address = COALESCE(excluded.address, customers.address),
                        last_contact = excluded.last_contact
                """, (customer_name, phone, customer_email or '', service_address, datetime.now(TIMEZONE).isoformat()))
        except Exception as e:
            print(f"Failed to save customer to dashboard DB: {e}")
        
        # Send confirmation email for non-emergency bookings
        if customer_email and urgency.lower() != "emergency":
            from emailer import send_confirmation_email
            email_result = send_confirmation_email(
                customer_email=customer_email,
                customer_name=customer_name,
                service_type=service_type,
                service_address=service_address,
                service_date=resolved_date,
                service_time=preferred_time,
                problem_description=problem_description,
                urgency=urgency,
            )
            result["email_sent"] = email_result.get("success", False)
            if not email_result.get("success"):
                result["email_error"] = email_result.get("error")
    
    return result


def cancel_appointment(customer_name: str, phone: str, appointment_date: str) -> dict:
    """
    Cancel appointment wrapper - requires event_id from calendar.
    For now returns placeholder since we need to look up by customer/date.
    """
    # This would need a lookup by customer_name + appointment_date to get event_id
    # For now, return not implemented
    return {
        "success": False,
        "message": "Cancellation requires event ID. Please contact the office directly."
    }


# ------------------------------------------------------------
# Function: check_availability
# Check if a time slot is available for booking
# ------------------------------------------------------------

def check_availability(preferred_date: str, preferred_time: str, service_name: str) -> dict:
    """
    Check if a time slot is available for a given service.
    Accepts 12-hour format (e.g., '2:30 PM') and converts to 24-hour internally.
    """
    from gcal.book_appointment import check_availability as cal_check_availability
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import os

    tz = ZoneInfo(os.getenv("TIMEZONE", "UTC"))
    resolved_date = resolve_relative_date(preferred_date)
    
    # Convert 12-hour format to 24-hour format
    time_24hr = parse_12hr_time(preferred_time)
    start_str = f"{resolved_date} {time_24hr}"

    try:
        start = datetime.strptime(start_str, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError:
        return {"success": False, "message": "Invalid date/time format. Use YYYY-MM-DD and time like '2:30 PM'"}

    service_lower = service_name.lower().strip()
    duration = SERVICES_DB.get(service_lower, {}).get("duration", 60)
    end = start + timedelta(minutes=duration)

    available = cal_check_availability(start, end)

    return {
        "success": True,
        "available": available,
        "date": resolved_date,
        "time": preferred_time,
        "service": service_lower,
        "duration_minutes": duration,
        "message": f"Slot is {'available' if available else 'NOT available'} for {service_lower} ({duration} min)"
    }


# ------------------------------------------------------------
# Function: get_customer_appointments
# Get upcoming service calls for a customer
# ------------------------------------------------------------

def get_customer_appointments(customer_name: str, phone: str) -> dict:
    """
    Get upcoming service calls for a customer.
    """
    from gcal.db import get_conn
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import os

    tz = ZoneInfo(os.getenv("TIMEZONE", "UTC"))
    now = datetime.now(tz).isoformat()

    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM appointments
            WHERE patient_name = ? AND datetime(start_time) >= datetime(?)
            ORDER BY start_time ASC
        """, (customer_name, now)).fetchall()

    appointments = []
    for row in rows:
        appointments.append({
            "event_id": row["google_event_id"],
            "service": row["service_name"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
        })

    return {
        "success": True,
        "customer_name": customer_name,
        "appointments": appointments,
        "count": len(appointments)
    }


# ------------------------------------------------------------
# Function 2: get_service_info
# Booking-only version. No pricing system yet.
# ------------------------------------------------------------

def get_service_info(service_name: str):
    """
    Get basic information about a plumbing service.
    No pricing is included yet.
    """
    service = SERVICES_DB.get(service_name.lower())

    if service:
        return {
            "service_name": service_name.lower(),
            "duration_minutes": service["duration"],
            "pricing": "Pricing is not available through the automated booking line. The plumber will provide an estimate after assessing the issue.",
            "message": f"{service_name.title()} service calls usually take about {service['duration']} minutes."
        }

    return {
        "error": f"Service '{service_name}' not found."
    }


# ------------------------------------------------------------
# Function map used by main.py
# These names must match config.json
# ------------------------------------------------------------

FUNCTION_MAP = {
    "lookup_customer": lookup_customer,
    "get_service_info": get_service_info,
    "resolve_relative_date": resolve_relative_date,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "check_availability": check_availability,
    "get_customer_appointments": get_customer_appointments,
}