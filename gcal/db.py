import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "calendar.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                patient_phone TEXT,
                google_event_id TEXT UNIQUE NOT NULL,
                service_name TEXT,
                start_time TEXT,
                end_time TEXT,
                sms_consent INTEGER DEFAULT 0,
                reminder_24h_sent INTEGER DEFAULT 0,
                reminder_2h_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_id ON appointments(google_event_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_phone ON appointments(patient_phone)")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_appointment(patient_name, patient_phone, google_event_id, service_name, start_time, end_time, sms_consent=False):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO appointments
            (patient_name, patient_phone, google_event_id, service_name, start_time, end_time, sms_consent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (patient_name, patient_phone, google_event_id, service_name, start_time, end_time, int(sms_consent)))


def get_appointment_by_event_id(event_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM appointments WHERE google_event_id = ?", (event_id,)).fetchone()


def get_upcoming_appointments(hours_ahead=24):
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM appointments
            WHERE datetime(start_time) BETWEEN datetime('now') AND datetime('now', ?)
            AND sms_consent = 1
        """, (f"+{hours_ahead} hours",)).fetchall()


def mark_reminder_sent(event_id, reminder_type):
    with get_conn() as conn:
        conn.execute(
            f"UPDATE appointments SET reminder_{reminder_type}_sent = 1 WHERE google_event_id = ?",
            (event_id,)
        )


def is_reminder_sent(event_id, reminder_type):
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT reminder_{reminder_type}_sent FROM appointments WHERE google_event_id = ?",
            (event_id,)
        ).fetchone()
        return row and row[0] == 1