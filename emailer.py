import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME = os.getenv("FROM_NAME", "RapidFlow Plumbing")

RESEND_API_URL = "https://api.resend.com/emails"


def _send_email(to_email: str, subject: str, html_body: str, text_body: str = None) -> dict:
    """Internal helper to send email via Resend API."""
    try:
        if not RESEND_API_KEY:
            return {"success": False, "error": "RESEND_API_KEY not configured in .env"}

        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            payload["text"] = text_body

        response = requests.post(RESEND_API_URL, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            return {"success": True, "message": "Email sent via Resend", "id": response.json().get("id")}
        else:
            return {"success": False, "error": f"Resend API error: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def send_confirmation_email(
    customer_email: str,
    customer_name: str,
    service_type: str,
    service_address: str,
    service_date: str,
    service_time: str,
    problem_description: str,
    urgency: str,
) -> dict:
    """
    Send appointment confirmation email to customer.
    Returns: {"success": bool, "message": str, "error": str}
    """
    subject = f"Service Call Confirmed - {service_type.title()} on {service_date} at {service_time}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a56db;">Service Call Confirmed</h2>
            <p>Dear {customer_name},</p>
            <p>Your plumbing service call has been confirmed.</p>
            
            <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1e293b;">Service Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px 0; font-weight: bold;">Service Type:</td><td>{service_type.title()}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Date:</td><td>{service_date}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Time:</td><td>{service_time}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Address:</td><td>{service_address}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Problem:</td><td>{problem_description}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Urgency:</td><td>{urgency.title()}</td></tr>
                </table>
            </div>
            
            <p>A licensed plumber will arrive at the scheduled time. Please ensure someone is available at the address.</p>
            <p>If you need to reschedule or cancel, please call us at least 2 hours before your appointment.</p>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #64748b; font-size: 14px;">Thank you for choosing RapidFlow Plumbing!<br>RapidFlow Plumbing Team</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""Dear {customer_name},

Your plumbing service call has been confirmed.

Service Details:
- Service Type: {service_type.title()}
- Date: {service_date}
- Time: {service_time}
- Address: {service_address}
- Problem: {problem_description}
- Urgency: {urgency.title()}

A licensed plumber will arrive at the scheduled time. Please ensure someone is available at the address.

If you need to reschedule or cancel, please call us at least 2 hours before your appointment.

Thank you for choosing RapidFlow Plumbing!

Best regards,
RapidFlow Plumbing Team
"""

    return _send_email(customer_email, subject, html_body, text_body)


def send_reschedule_email(
    customer_email: str,
    customer_name: str,
    service_type: str,
    old_date: str,
    old_time: str,
    new_date: str,
    new_time: str,
) -> dict:
    """Send reschedule notification email."""
    subject = f"Service Call Rescheduled - {service_type.title()}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a56db;">Service Call Rescheduled</h2>
            <p>Dear {customer_name},</p>
            <p>Your plumbing service call has been rescheduled.</p>
            
            <div style="background: #fef3c7; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                <h3 style="margin-top: 0; color: #92400e;">Previous Appointment</h3>
                <p>Date: {old_date}<br>Time: {old_time}</p>
            </div>
            
            <div style="background: #d1fae5; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #10b981;">
                <h3 style="margin-top: 0; color: #065f46;">New Appointment</h3>
                <p>Date: {new_date}<br>Time: {new_time}<br>Service: {service_type.title()}</p>
            </div>
            
            <p>Please confirm this new time works for you. If not, call us to adjust.</p>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #64748b; font-size: 14px;">Thank you,<br>RapidFlow Plumbing Team</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""Dear {customer_name},

Your plumbing service call has been rescheduled.

Previous Appointment:
- Date: {old_date}
- Time: {old_time}

New Appointment:
- Date: {new_date}
- Time: {new_time}
- Service: {service_type.title()}

Please confirm this new time works for you. If not, call us to adjust.

Thank you,
RapidFlow Plumbing Team
"""

    return _send_email(customer_email, subject, html_body, text_body)


def send_cancellation_email(
    customer_email: str,
    customer_name: str,
    service_type: str,
    cancelled_date: str,
    cancelled_time: str,
) -> dict:
    """Send cancellation confirmation email."""
    subject = f"Service Call Cancelled - {service_type.title()}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #ef4444;">Service Call Cancelled</h2>
            <p>Dear {customer_name},</p>
            <p>Your plumbing service call has been cancelled.</p>
            
            <div style="background: #fef2f2; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #ef4444;">
                <h3 style="margin-top: 0; color: #991b1b;">Cancelled Appointment</h3>
                <p>Service: {service_type.title()}<br>Date: {cancelled_date}<br>Time: {cancelled_time}</p>
            </div>
            
            <p>If you need to reschedule, please call us.</p>
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #64748b; font-size: 14px;">Thank you,<br>RapidFlow Plumbing Team</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""Dear {customer_name},

Your plumbing service call has been cancelled.

Cancelled Appointment:
- Service: {service_type.title()}
- Date: {cancelled_date}
- Time: {cancelled_time}

If you need to reschedule, please call us.

Thank you,
RapidFlow Plumbing Team
"""

    return _send_email(customer_email, subject, html_body, text_body)