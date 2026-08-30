from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sqlite3
import os
import json
from contextlib import contextmanager

app = FastAPI(title="RapidFlow Plumbing API")

DB_PATH = "calendar.db"
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/New_York"))

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_dashboard_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_contact TEXT,
                UNIQUE(name, phone)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                booking_id TEXT,
                email_type TEXT,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1
            )
        """)

init_dashboard_db()

class BookingCreate(BaseModel):
    customer_name: str
    phone: str
    email: Optional[str] = None
    service_address: str
    service_type: str
    problem_description: str
    urgency: str
    preferred_date: str
    preferred_time: str

@app.get("/api/bookings")
async def get_bookings(
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None
):
    with get_conn() as conn:
        query = "SELECT * FROM appointments WHERE 1=1"
        params = []
        if month and year:
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year+1}-01-01"
            else:
                end = f"{year}-{month+1:02d}-01"
            query += " AND date(start_time) >= ? AND date(start_time) < ?"
            params.extend([start, end])
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY start_time ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

@app.post("/api/bookings")
async def create_booking(booking: BookingCreate):
    from gcal.book_appointment import create_appointment as gcal_create
    from receptionist_functions import resolve_relative_date, parse_12hr_time

    resolved_date = resolve_relative_date(booking.preferred_date)
    time_24hr = parse_12hr_time(booking.preferred_time)
    start_str = f"{resolved_date} {time_24hr}"

    result = gcal_create(
        patient_name=booking.customer_name,
        service_name=booking.service_type.lower().strip(),
        start_str=start_str,
        patient_phone=booking.phone,
        sms_consent=False,
    )

    if result.get("success"):
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO customers (name, phone, email, address, last_contact) VALUES (?, ?, ?, ?, ?)",
                (booking.customer_name, booking.phone, booking.email or '', booking.service_address, datetime.now(TIMEZONE).isoformat())
            )
            customer_id = cursor.lastrowid
            if customer_id == 0:
                row = conn.execute("SELECT id FROM customers WHERE phone = ?", (booking.phone,)).fetchone()
                customer_id = row["id"] if row else None

            if booking.email and booking.urgency.lower() != "emergency":
                conn.execute(
                    "INSERT INTO email_logs (customer_id, booking_id, email_type, success) VALUES (?, ?, ?, ?)",
                    (customer_id, result.get("event_id"), "confirmation", 1)
                )

    return result

@app.get("/api/customers")
async def get_customers():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM appointments WHERE patient_name = c.name) as booking_count
            FROM customers c
            ORDER BY c.created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]

@app.get("/api/emails")
async def get_email_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) as count FROM email_logs WHERE success = 1").fetchone()
        return {"sent": total["count"] if total else 0}

@app.delete("/api/bookings")
async def delete_booking(event_id: str = Query(...)):
    from gcal.book_appointment import cancel_appointment
    from gcal.db import get_conn as gcal_get_conn
    result = cancel_appointment(event_id)
    if result.get("success"):
        with get_conn() as conn:
            conn.execute("DELETE FROM appointments WHERE google_event_id = ?", (event_id,))
    return result

# New endpoint to clear all appointments (used for bulk delete of test data)
@app.post("/api/clear")
async def clear_all_appointments():
    with get_conn() as conn:
        # Remove all appointments
        conn.execute("DELETE FROM appointments")
        # Optionally clean up email logs related to those appointments
        conn.execute("DELETE FROM email_logs")
    return {"cleared": True}
@app.get("/api/analytics")
async def get_analytics():
    with get_conn() as conn:
        now = datetime.now(TIMEZONE)
        this_month_start = now.replace(day=1).isoformat()
        last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()

        this_month = conn.execute(
            "SELECT COUNT(*) as count FROM appointments WHERE start_time >= ?", (this_month_start,)
        ).fetchone()
        last_month = conn.execute(
            "SELECT COUNT(*) as count FROM appointments WHERE start_time >= ? AND start_time < ?", 
            (last_month_start, this_month_start)
        ).fetchone()

        this_count = this_month["count"] if this_month else 0
        last_count = last_month["count"] if last_month else 0
        growth = round(((this_count - last_count) / last_count * 100) if last_count > 0 else 0, 1)

        chart_rows = conn.execute("""
            SELECT strftime('%Y-%m', start_time) as month, COUNT(*) as count
            FROM appointments
            WHERE start_time >= date('now', '-11 months')
            GROUP BY strftime('%Y-%m', start_time)
            ORDER BY month
        """).fetchall()

        chart_data = [{"month": row["month"], "count": row["count"]} for row in chart_rows]

        return {
            "monthly_bookings": this_count,
            "growth": growth,
            "avg_value": 150,
            "chart_data": chart_data
        }

@app.get("/api/records")
async def get_records(
    search: str = "",
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit
    with get_conn() as conn:
        query = """
            SELECT a.*, 
                   c.email as customer_email,
                   (SELECT COUNT(*) FROM email_logs WHERE booking_id = a.google_event_id AND success = 1) as email_sent
            FROM appointments a
            LEFT JOIN customers c ON c.name = a.patient_name
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (a.patient_name LIKE ? OR a.patient_phone LIKE ? OR c.email LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        query += " ORDER BY a.start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        total_query = "SELECT COUNT(*) as count FROM appointments a LEFT JOIN customers c ON c.name = a.patient_name WHERE 1=1"
        if search:
            total_query += " AND (a.patient_name LIKE ? OR a.patient_phone LIKE ? OR c.email LIKE ?)"
        total = conn.execute(total_query, params[:3] if search else []).fetchone()

        return {
            "records": [dict(row) for row in rows],
            "total": total["count"] if total else 0
        }

app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)