import json

prompt = """You are a professional dental receptionist at Bright Smile Dental Clinic. Your goal is to provide warm, efficient, and professional service to every caller. 

**CURRENT DATE: August 21, 2026 (Thursday)** - Use this as 'today' for all date references.

Follow this exact conversation flow:

**STEP 1 - GREETING:**
Start every call with: 'Good [morning/afternoon/evening]! Thank you for calling Bright Smile Dental. How may I help you today?'

**STEP 2 - UNDERSTAND NEED:**
Listen carefully to what the patient needs:
- Booking a new appointment
- Cancelling an existing appointment
- Asking about dental services
- Emergency dental care
- General inquiries

**STEP 3 - FOR BOOKING APPOINTMENTS:**
Collect information ONE piece at a time. Ask politely:

A) 'May I have your full name, please?'
   - Wait for response
   - If name is unclear, ask: 'Could you please spell that for me?'

B) 'May I have your age, please?'
   - Wait for response

C) 'What service are you looking for today?'
   - Offer options: cleaning, checkup, filling, crown, root canal, extraction, whitening, or consultation
   - If they're unsure, say: 'Let me help you decide. What dental concern do you have?'

D) 'What date would you prefer for your appointment?'
   - Use resolve_relative_date if they say 'tomorrow', 'next week', 'in 3 days', etc.
   - If no date given, ask: 'Would you prefer a morning or afternoon appointment?'

E) Check availability and offer specific times:
   - 'We have availability on [date] at [time1] or [time2]. Which works better for you?'
   - If those times don't work, ask: 'What time would be more convenient for you?'

**STEP 4 - CONFIRM ALL DETAILS:**
Before booking, confirm everything:
- 'Let me confirm: [Patient Name], age [Age], [Service] appointment on [Date] at [Time]. Is that correct?'
- If they say no, correct the information and confirm again

**STEP 5 - BOOK APPOINTMENT:**
Call book_appointment with:
- patient_name: Full name provided
- age: Age provided
- service_name: The service they want
- start_str: Date and time in YYYY-MM-DD HH:MM format

**STEP 6 - PROFESSIONAL CLOSING:**
End the call warmly:
- 'Your appointment is confirmed! We look forward to seeing you on [Date] at [Time]. Have a great day!'"""

config = {
    "type": "Settings",
    "audio": {
        "input": {"encoding": "mulaw", "sample_rate": 8000},
        "output": {"encoding": "mulaw", "sample_rate": 8000, "container": "none"}
    },
    "agent": {
        "language": "en",
        "listen": {"provider": {"type": "deepgram", "model": "nova-3", "keyterms": ["hello", "goodbye"]}},
        "think": {
            "provider": {"type": "open_ai", "model": "gpt-4o-mini", "temperature": 0.7},
            "prompt": prompt,
            "functions": [
                {"name": "book_appointment", "description": "Book a new dental appointment for a patient. Use this when a patient wants to schedule a cleaning, checkup, filling, crown, root canal, extraction, whitening, or consultation. Before booking: verify patient exists with lookup_patient (or collect new patient info). Get preferred date/time and procedure type. Confirm all details with the patient.", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string", "description": "Patient's full legal name"}, "age": {"type": "integer", "description": "Patient's age"}, "preferred_date": {"type": "string", "description": "Preferred appointment date in YYYY-MM-DD format (e.g., 2026-01-15 or 'tomorrow', 'next monday')"}, "preferred_time": {"type": "string", "description": "Preferred appointment time in HH:MM format (24-hour, e.g., 14:30)"}, "procedure_type": {"type": "string", "description": "Type of procedure: 'cleaning', 'checkup', 'filling', 'crown', 'root canal', 'extraction', 'whitening', 'consultation'"}, "is_new_patient": {"type": "boolean", "description": "Whether this is a new patient"}}, "required": ["patient_name", "age", "preferred_date", "preferred_time", "procedure_type"]}},
                {"name": "cancel_appointment", "description": "Cancel an existing appointment. Use this when a patient wants to cancel their appointment. Requires patient name and age to verify identity.", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string", "description": "Patient's full legal name"}, "age": {"type": "integer", "description": "Patient's age"}, "appointment_date": {"type": "string", "description": "Date of appointment to cancel in YYYY-MM-DD format"}}, "required": ["patient_name", "age", "appointment_date"]}},
                {"name": "lookup_patient", "description": "Look up an existing patient record. Use this when a patient calls about their account or wants to verify their information. Always verify identity with full name and age before sharing any information.", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string", "description": "Patient's full legal name"}, "age": {"type": "integer", "description": "Patient's age"}}, "required": ["patient_name", "age"]}},
                {"name": "get_service_info", "description": "Get information about a dental service including duration. Use this when a caller asks about a specific procedure.", "parameters": {"type": "object", "properties": {"service_name": {"type": "string", "description": "Name of the service: 'cleaning', 'checkup', 'filling', 'crown', 'root canal', 'extraction', 'whitening', 'consultation'"}}, "required": ["service_name"]}},
                {"name": "resolve_relative_date", "description": "Convert relative date expressions like 'tomorrow', 'next monday', 'in 3 days' to YYYY-MM-DD format. Use this when a patient gives a relative date for an appointment.", "parameters": {"type": "object", "properties": {"relative_date": {"type": "string", "description": "Relative date expression: 'today', 'tomorrow', 'next monday', 'in 3 days', etc."}}, "required": ["relative_date"]}},
                {"name": "check_availability", "description": "Check if a specific date/time slot is available for a dental service. Use this before booking to confirm availability.", "parameters": {"type": "object", "properties": {"preferred_date": {"type": "string", "description": "Preferred date in YYYY-MM-DD format or relative like 'tomorrow', 'next monday'"}, "preferred_time": {"type": "string", "description": "Preferred time in HH:MM format (24-hour, e.g., 14:30)"}, "service_name": {"type": "string", "description": "Service type: 'cleaning', 'checkup', 'filling', 'crown', 'root canal', 'extraction', 'whitening', 'consultation'"}}, "required": ["preferred_date", "preferred_time", "service_name"]}},
                {"name": "get_patient_appointments", "description": "Get all upcoming appointments for a patient. Use this when a patient asks about their existing appointments.", "parameters": {"type": "object", "properties": {"patient_name": {"type": "string", "description": "Patient's full legal name"}, "age": {"type": "integer", "description": "Patient's age"}}, "required": ["patient_name", "age"]}}
            ]
        },
        "speak": {"provider": {"type": "deepgram", "model": "flux-priya-en"}},
        "greeting": "Bright Smile Dental. What is your reason for calling?"
    }
}

with open("config.json", "w") as f:
    json.dump(config, f, indent=2)

print("config.json fixed")