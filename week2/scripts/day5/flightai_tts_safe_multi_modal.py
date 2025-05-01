"""
FlightAI Chatbot: Voice Input, GPT-4o Chat, DALL-E 3 Image, Auto TTS, Live Timer, Booking System, Booking Viewer, Translation Agent (now with Chinese!)
"""

# (imports unchanged)
import os
import json
import base64
import csv
import re
import time
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play
import gradio as gr

# 1. Setup
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")
client = OpenAI(api_key=api_key)
translation_client = OpenAI(api_key=api_key)  # Same or different key/model if needed
MODEL = "gpt-4o"
OUTPUT_DIR = "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


class SessionState:
    def __init__(self):
        self.current_city = ""
        self.chat_log = []
        self.total_cost = 0.0
        self.record_start_time = None


session = SessionState()

system_message = (
    "You are a helpful assistant for an Airline called FlightAI. "
    "Give short, courteous answers. If a destination is discussed, generate an image and optionally speak the reply. "
    "If a booking is made, confirm it nicely with the booking ID."
)

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}


def get_ticket_price(destination_city):
    return ticket_prices.get(destination_city.lower(), "Unknown")


def make_booking(destination_city, passenger_name):
    booking_time = datetime.now().isoformat()
    booking_id = f"{passenger_name[:3].upper()}{int(time.time())}"
    with open(os.path.join(OUTPUT_DIR, "bookings.csv"), "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([booking_id, passenger_name, destination_city, booking_time])
    return {
        "booking_id": booking_id,
        "destination_city": destination_city,
        "passenger_name": passenger_name,
        "booking_time": booking_time
    }


def show_all_bookings():
    bookings_path = os.path.join(OUTPUT_DIR, "bookings.csv")
    if not os.path.exists(bookings_path):
        return "No bookings yet."

    output = "### ✈️ Current Bookings:\n\n"
    with open(bookings_path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return "No bookings yet."

        for row in rows:
            if len(row) == 4:
                booking_id, passenger, destination, time_created = row
                output += f"- **Booking ID**: `{booking_id}` | **Passenger**: {passenger} | **Destination**: {destination} | **Time**: {time_created}\n"
    return output


def handle_tool_call(tool_call):
    args = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "get_ticket_price":
        city = args.get("destination_city", "").strip()
        price = get_ticket_price(city)
        return {"role": "tool", "tool_call_id": tool_call.id,
                "content": json.dumps({"destination_city": city, "price": price})}, city
    elif tool_call.function.name == "make_booking":
        city = args.get("destination_city", "").strip()
        passenger = args.get("passenger_name", "").strip()
        booking_info = make_booking(city, passenger)
        return {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(booking_info)}, city
    else:
        return {"role": "tool", "tool_call_id": tool_call.id, "content": "Unknown tool call."}, ""


def log_usage(feature, cost=0.0):
    session.total_cost += cost
    with open(os.path.join(OUTPUT_DIR, "usage_log.csv"), "a", newline="") as f:
        csv.writer(f).writerow([datetime.now().isoformat(), feature, f"{cost:.4f}"])


def artist(city):
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"A vacation scene in {city}, charcoal sketch style",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    log_usage("image_generation", 0.08)
    image_data = base64.b64decode(image_response.data[0].b64_json)
    filepath = os.path.join(OUTPUT_DIR, f"{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    with open(filepath, "wb") as f:
        f.write(image_data)
    return Image.open(BytesIO(image_data))


def clean_for_tts(text):
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[\*\_\#\>`]', '', text)
    return text.strip()


def talker(message):
    message = clean_for_tts(message)
    if len(message) > 400:
        log_usage("tts_skipped", 0.0)
        return
    response = client.audio.speech.create(model="tts-1", voice="onyx", input=message)
    cost = (len(message) / 1000) * 0.015
    log_usage("tts", round(cost, 4))
    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)


def translate_text(original_text, target_language):
    try:
        response = translation_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a translator. Translate into {target_language}."},
                {"role": "user", "content": original_text}
            ],
            temperature=0.3,
        )
        translation = response.choices[0].message.content
        return translation
    except Exception as e:
        return f"⚠️ Translation failed: {str(e)}"


def chat(history, enable_image, enable_tts):
    messages = [{"role": "system", "content": system_message}] + history
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_ticket_price",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination_city": {"type": "string"}
                            },
                            "required": ["destination_city"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "make_booking",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination_city": {"type": "string"},
                                "passenger_name": {"type": "string"}
                            },
                            "required": ["destination_city", "passenger_name"]
                        }
                    }
                }
            ]
        )
        log_usage("chat")
    except OpenAIError as e:
        history.append({"role": "assistant", "content": f"⚠️ OpenAI error: {e}"})
        return history, None

    if response.choices[0].finish_reason == "tool_calls":
        tool_call_msg = response.choices[0].message
        tool_call = tool_call_msg.tool_calls[0]
        tool_response, city = handle_tool_call(tool_call)
        session.current_city = city
        messages.append(
            {"role": "assistant", "content": tool_call_msg.content or "", "tool_calls": tool_call_msg.tool_calls})
        messages.append(tool_response)
        try:
            response = client.chat.completions.create(model=MODEL, messages=messages)
            log_usage("chat")
        except OpenAIError as e:
            history.append({"role": "assistant", "content": f"⚠️ OpenAI error after tool use: {e}"})
            return history, None

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    session.chat_log.append({"user": history[-2]["content"], "assistant": reply})

    if enable_tts and reply:
        talker(reply)

    return history, reply


def start_recording():
    session.record_start_time = time.time()
    return "🎤 Recording..."


def listen_and_transcribe(audio_path):
    if audio_path is None:
        return "No audio recorded.", ""
    elapsed = time.time() - session.record_start_time if session.record_start_time else 0
    try:
        with open(audio_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        log_usage("audio_transcription", 0.006)
        return f"Recording stopped. Duration: {elapsed:.1f} seconds", transcript_response
    except Exception as e:
        return f"⚠️ Error: {e}", ""


with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
        translation_output = gr.Markdown("### Translation will appear here")

    with gr.Row():
        entry = gr.Textbox(label="Ask FlightAI:")

    with gr.Row():
        mic = gr.Audio(type="filepath", format="wav", label="🎤 Speak to FlightAI")
        record_timer = gr.Markdown("Recording status...")
        audio_transcript = gr.Textbox(label="Transcribed Text (Editable)")

    with gr.Row():
        enable_image = gr.Checkbox(label="Enable Image Generation", value=False)
        enable_tts = gr.Checkbox(label="Enable Text-to-Speech", value=True)
        language_selector = gr.Dropdown(["French", "Spanish", "German", "Japanese", "Chinese"],
                                        label="Translation Language", value="French")
        test_tts_button = gr.Button("Test TTS Voice")

    with gr.Row():
        clear = gr.Button("Clear")
        show_bookings = gr.Button("Show My Bookings")

    with gr.Row():
        cost_display = gr.Markdown("**Total Estimated Cost: $0.00**")


    def do_entry(message, history):
        history.append({"role": "user", "content": message})
        return "", history


    def process_chat(history, enable_image_flag, enable_tts_flag, target_language):
        updated_history, reply = chat(history, enable_image_flag, enable_tts_flag)
        translation = ""
        if reply:
            translation = translate_text(reply, target_language)

        if enable_image_flag and session.current_city:
            image = artist(session.current_city)
            return updated_history, image, f"**Total Estimated Cost: ${session.total_cost:.2f}**", translation
        return updated_history, None, f"**Total Estimated Cost: ${session.total_cost:.2f}**", translation


    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        process_chat,
        inputs=[chatbot, enable_image, enable_tts, language_selector],
        outputs=[chatbot, image_output, cost_display, translation_output]
    )

    mic.start_recording(start_recording, outputs=[record_timer])
    mic.change(listen_and_transcribe, inputs=[mic], outputs=[record_timer, audio_transcript]).then(
        do_entry,
        inputs=[audio_transcript, chatbot],
        outputs=[entry, chatbot]
    ).then(
        process_chat,
        inputs=[chatbot, enable_image, enable_tts, language_selector],
        outputs=[chatbot, image_output, cost_display, translation_output]
    )

    test_tts_button.click(lambda: talker("Hello, welcome to FlightAI! This is a TTS test."), outputs=[])
    clear.click(lambda: [], outputs=chatbot, queue=False)
    show_bookings.click(lambda: [{"role": "assistant", "content": show_all_bookings()}], outputs=chatbot)

ui.launch(inbrowser=True)
