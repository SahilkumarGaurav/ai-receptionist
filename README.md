# Voice Dental Receptionist

A real-time voice AI system that handles dental office phone calls using Twilio for telephony and Deepgram for speech-to-text, LLM reasoning, and text-to-speech.

## Features

- **Voice-based patient interaction** - Patients can inquire about services, check patient records, and get information via phone
- **Real-time audio streaming** - Bidirectional mulaw 8kHz audio between Twilio and Deepgram
- **Natural language date parsing** - Understands "today", "tomorrow", "next Monday", "in 3 days"
- **Barge-in support** - Detects when patient starts speaking and interrupts AI response
- **Multi-service support** - Cleaning, checkup, filling, crown, root canal, extraction, whitening, consultation

## Architecture

```
Caller (Phone) → Twilio → WebSocket Server (main.py) → Deepgram Agent API
                                                    ↓
                                           Function Calls (receptionist_functions.py)
```

## Components

| File | Purpose |
|------|---------|
| `main.py` | WebSocket server handling Twilio ↔ Deepgram audio streaming |
| `receptionist_functions.py` | Dental functions (patient lookup, service info, date parsing) |
| `pharmacy_functions.py` | Separate pharmacy ordering module (not used in current config) |
| `config.json` | Deepgram agent configuration (STT, LLM, TTS, system prompt, functions) |

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or with uv:
   uv sync
   ```

2. **Configure environment variables** (`.env`):
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   TIMEZONE=America/New_York
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```
   Server starts on `localhost:5000`

4. **Configure Twilio webhook:**
   - Point your Twilio phone number's voice webhook to `wss://your-domain/websocket` (or use ngrok for local testing)

## Function Reference

### Dental Receptionist Functions

- `lookup_patient(patient_id, patient_name)` - Finds patient record (placeholder)
- `get_service_info(service_name)` - Returns service duration/description
- `resolve_relative_date(relative_date)` - Converts "tomorrow" → "2026-08-15"

### Pharmacy Functions (standalone)

- `get_drug_info(drug_name)` - Drug details and pricing
- `place_order(customer_name, drug_name)` - Creates order
- `lookup_order(order_id)` - Checks order status

## Configuration

The `config.json` defines the Deepgram agent:
- **STT**: Nova-3 model
- **LLM**: GPT-4o-mini with dental receptionist system prompt
- **TTS**: Aura-2-Thalia voice
- **Functions**: 3 function definitions matching `FUNCTION_MAP` in receptionist_functions.py