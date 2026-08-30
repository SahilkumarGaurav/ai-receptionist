import asyncio
import base64
import json
import websockets
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from receptionist_functions import FUNCTION_MAP
from gcal.reminders import start_scheduler, stop_scheduler

load_dotenv()


def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not found")

    return websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )


def get_greeting_time():
    """Return 'morning', 'afternoon', or 'evening' based on current time."""
    tz_name = os.getenv("TIMEZONE", "UTC")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    hour = now.hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    else:
        return "evening"


def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Inject current date and time for the AI
    tz_name = os.getenv("TIMEZONE", "UTC")
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    current_date = now.strftime("%B %d, %Y (%A)")
    current_time = now.strftime("%I:%M %p")
    greeting = get_greeting_time()
    
    # Replace placeholders in the prompt
    prompt = config["agent"]["think"]["prompt"]
    prompt = prompt.replace("**CURRENT DATE: August 21, 2026 (Thursday)**", 
                           f"**CURRENT DATE: {current_date}**")
    prompt = prompt.replace("Good [morning/afternoon/evening]!", 
                           f"Good {greeting}!")
    config["agent"]["think"]["prompt"] = prompt
    
    return config


async def handle_barge_in(decoded, twilio_ws, streamsid):
    if decoded["type"] == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send(json.dumps(clear_message))


def execute_function_call(func_name, arguments):
    if func_name in FUNCTION_MAP:
        result = FUNCTION_MAP[func_name](**arguments)
        print(f"Function call result: {result}")
        return result
    else:
        result = {"error": f"Unknown function: {func_name}"}
        print(result)
        return result


def create_function_call_response(func_id, func_name, result):
    return {
        "type": "FunctionCallResponse",
        "id": func_id,
        "name": func_name,
        "content": json.dumps(result)
    }


async def handle_function_call_request(decoded, sts_ws):
    try:
        for function_call in decoded["functions"]:
            func_name = function_call["name"]
            func_id = function_call["id"]
            arguments = json.loads(function_call["arguments"])

            print(f"Function call: {func_name} (ID: {func_id}), arguments: {arguments}")

            result = execute_function_call(func_name, arguments)

            function_result = create_function_call_response(func_id, func_name, result)
            await sts_ws.send(json.dumps(function_result))
            print(f"Sent function result: {function_result}")

    except Exception as e:
        print(f"Error calling function: {e}")
        error_result = create_function_call_response(
            func_id if "func_id" in locals() else "unknown",
            func_name if "func_name" in locals() else "unknown",
            {"error": f"Function call failed with: {str(e)}"}
        )
        await sts_ws.send(json.dumps(error_result))


async def handle_text_message(decoded, twilio_ws, sts_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)

    if decoded["type"] == "FunctionCallRequest":
        await handle_function_call_request(decoded, sts_ws)


async def sts_sender(sts_ws, audio_queue):
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)


async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    streamsid = await streamsid_queue.get()

    async for message in sts_ws:
        if isinstance(message, str):
            # Deepgram sends JSON strings for textual responses and function calls.
            # Print a clean transcript of the assistant's spoken text while leaving function
            # call handling untouched.
            decoded = json.loads(message)
            # Transcription handling – print only the actual spoken content.
            # Deepgram's agent may embed the text directly in "content", or inside a nested
            # "message" dictionary.  Fallback to the raw decoded payload if we cannot locate it.
            content = decoded.get("content")
            if not content:
                # Some responses are wrapped as {"message": {"role": "assistant", "content": "..."}}
                msg_obj = decoded.get("message")
                if isinstance(msg_obj, dict):
                    content = msg_obj.get("content") or msg_obj.get("message")
                else:
                    content = msg_obj
            if content:
                print(f"[TRANSCRIPT] {content}")
            else:
                # If we cannot extract a clean string, fall back to printing the raw JSON for debugging.
                print(f"[TRANSCRIPT] {decoded}")
            
            await handle_text_message(decoded, twilio_ws, sts_ws, streamsid)
            continue
            
            # Binary mulaw audio from Deepgram – forward to Twilio.
            raw_mulaw = message
            media_message = {
                "event": "media",
                "streamSid": streamsid,
                "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")}
            }
            await twilio_ws.send(json.dumps(media_message))


async def twilio_receiver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray(b"")

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            event = data["event"]

            if event == "start":
                start = data["start"]
                streamsid = start["streamSid"]
                streamsid_queue.put_nowait(streamsid)
            elif event == "connected":
                continue
            elif event == "media":
                media = data["media"]
                chunk = base64.b64decode(media["payload"])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)
            elif event == "stop":
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]
        except Exception as e:
            break


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.wait(
            [
                asyncio.ensure_future(sts_sender(sts_ws, audio_queue)),
                asyncio.ensure_future(sts_receiver(sts_ws, twilio_ws, streamsid_queue)),
                asyncio.ensure_future(twilio_receiver(twilio_ws, audio_queue, streamsid_queue)),
            ]
        )

        await twilio_ws.close()


async def main():
    start_scheduler()
    # Determine a free port (default 5000) – if taken, try the next few ports.
    default_port = int(os.getenv("WS_PORT", "5000"))
    port = default_port
    while True:
        try:
            server = await websockets.serve(twilio_handler, "localhost", port)
            break
        except OSError as e:
            # WinError 10048 = address already in use (or errno 10048)
            if getattr(e, "winerror", None) == 10048 or getattr(e, "errno", None) == 10048:
                port += 1
                if port - default_port > 10:
                    raise RuntimeError(f"Could not bind to any port in range {default_port}-{default_port+10}")
                continue
            raise
    print(f"WebSocket server listening on ws://localhost:{port}")
    try:
        # Run forever until cancelled (Ctrl+C)
        await asyncio.Future()
    finally:
        # Clean shutdown: stop the scheduler and close the server
        server.close()
        await server.wait_closed()
        stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())