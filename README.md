# RapidFlow Plumbing Voice AI

A real-time voice AI system for plumbing service calls using Twilio for telephony, Deepgram for STT/TTS, OpenAI GPT-4o-mini for reasoning, and Google Calendar for scheduling.

## Features

- **Voice-based customer interaction** - Customers can request plumbing services, check availability, book appointments, and get service info via phone
- **Real-time audio streaming** - Bidirectional μ-law 8kHz audio between Twilio and Deepgram
- **Intelligent urgency triage** - Automatically classifies calls as Emergency, Urgent, or Standard based on problem description
- **Natural language date/time parsing** - Understands "today", "tomorrow", "next Monday", "in 3 days", "2:30 PM"
- **Barge-in support** - Detects when customer starts speaking and interrupts AI response
- **Google Calendar integration** - Books appointments directly to Google Calendar with conflict checking
- **Email confirmations** - Sends confirmation emails via Resend for non-emergency bookings
- **Automated reminders** - Background scheduler sends 24-hour and 2-hour appointment reminders
- **Customer database** - SQLite database stores customer info and appointment history

## Architecture

```
Caller (Phone) → Twilio → WebSocket Server (main.py) → Deepgram Agent API
                                                    ↓
                                          Function Calls (receptionist_functions.py)
                                                    ↓
                                            Google Calendar (gcal/) + SQLite DB
```

## Components

| File | Purpose |
|------|---------|
| `main.py` | WebSocket server handling Twilio ↔ Deepgram audio streaming, scheduler lifecycle |
| `receptionist_functions.py` | Core plumbing functions (booking, lookup, availability, date parsing, customer DB) |
| `emailer.py` | Email confirmation/reschedule/cancellation via Resend API |
| `config.json` | Deepgram agent config (STT, LLM, TTS, system prompt, function definitions) |
| `gcal/auth.py` | Google OAuth2 authentication for Calendar API |
| `gcal/service.py` | Google Calendar service client |
| `gcal/book_appointment.py` | Calendar booking logic with availability checking |
| `gcal/db.py` | SQLite database for appointments, customers, reminders |
| `gcal/reminders.py` | APScheduler background job for 24h/2h reminders |

## Services Offered

| Service | Duration |
|---------|----------|
| Leak Repair | 60 min |
| Clogged Drain | 45 min |
| Toilet Repair | 45 min |
| Water Heater | 90 min |
| Faucet Repair | 30 min |
| Sink Repair | 45 min |
| Sewer Service | 120 min |
| Pipe Repair | 90 min |
| Pipe Replacement | 120 min |
| Water Pressure | 45 min |
| No Hot Water | 60 min |
| Installation | 60 min |
| Inspection | 45 min |
| Emergency Plumbing | 60 min |
| General Plumbing | 60 min |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
# or with uv:
uv sync
```

### 2. Configure environment variables (`.env`)
```
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
GOOGLE_CALENDAR_ID=primary
TIMEZONE=America/New_York
RESEND_API_KEY=your_resend_key
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=RapidFlow Plumbing
WS_PORT=5000
```

### 3. Google Calendar Setup
1. Create a Google Cloud project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` in project root
5. First run will generate `token.json` via browser auth

### 4. Run the server
```bash
python main.py
```
Server starts on `ws://localhost:5000` (auto-increments port if busy)

### 5. Configure Twilio webhook
- Point your Twilio phone number's voice webhook to `wss://your-domain/websocket`
- Use ngrok for local testing: `ngrok http 5000` then use the https URL

## Function Reference

### Core Functions (exposed to Deepgram Agent)

| Function | Description |
|----------|-------------|
| `book_appointment` | Book new plumbing service call with full details |
| `cancel_appointment` | Cancel existing appointment (requires event ID lookup) |
| `lookup_customer` | Look up customer by name and phone |
| `get_service_info` | Get service duration and info (no pricing) |
| `resolve_relative_date` | Convert "tomorrow", "next monday" → YYYY-MM-DD |
| `check_availability` | Check if date/time slot is free for a service |
| `get_customer_appointments` | Get upcoming appointments for a customer |

### Book Appointment Parameters
- `customer_name` (required) - Full name
- `phone` (required) - Phone number
- `service_address` (required) - Service location
- `service_type` (required) - One of the services above
- `problem_description` (required) - Details for urgency classification
- `urgency` (required) - emergency, urgent, or standard
- `preferred_date` (required) - YYYY-MM-DD or relative
- `preferred_time` (required) - 12-hour format (e.g., "2:30 PM")
- `customer_email` (optional) - For confirmation email

## Configuration

`config.json` defines the Deepgram Agent:
- **STT**: Nova-3 model with plumbing keyterms
- **LLM**: GPT-4o-mini (temp 0.7) with detailed plumbing receptionist prompt
- **TTS**: Flux-Jack-EN voice
- **Functions**: 7 function definitions matching `FUNCTION_MAP`

The system prompt includes:
1. Greeting with time-of-day awareness
2. Structured conversation flow (greet → triage → collect details → book)
3. Automatic urgency classification (Emergency/Urgent/Standard)
4. Emergency safety protocols
5. Required data collection before booking

## Database Schema (SQLite - `calendar.db`)

- `appointments` - Google Calendar events with local metadata
- `customers` - Customer name, phone, email, address, last contact
- `reminders_sent` - Tracks 24h/2h reminder delivery per appointment

## API Keys Required

| Service | Purpose |
|---------|---------|
| Deepgram | STT + TTS (Nova-3, Flux-Jack) |
| OpenAI | LLM reasoning (GPT-4o-mini) |
| Google Cloud | Calendar API (OAuth2) |
| Resend | Email confirmations |
| Twilio | Phone number + WebSocket streaming |

## Development

### Project Structure
```
.
├── main.py                      # WebSocket server entry point
├── receptionist_functions.py    # Core business logic
├── emailer.py                   # Resend email integration
├── config.json                  # Deepgram agent configuration
├── gcal/                        # Google Calendar integration
│   ├── auth.py                  # OAuth2 flow
│   ├── service.py               # Calendar API client
│   ├── book_appointment.py      # Booking logic
│   ├── db.py                    # SQLite database
│   └── reminders.py             # APScheduler reminders
├── credentials.json             # Google OAuth credentials (gitignored)
├── token.json                   # Google OAuth token (gitignored)
├── .env                         # Environment variables (gitignored)
├── calendar.db                  # SQLite database (gitignored)
└── uv.lock                      # uv lock file (gitignored)
```

### Running Tests
```bash
# No formal test suite yet - test manually via Twilio/ngrok
```

## License

MIT