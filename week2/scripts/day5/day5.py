"""
Pedagogical Demo: FlightAI Chatbot with Tool Calling, Image Generation, and Text-to-Speech

This script demonstrates:
1. System prompt usage
2. OpenAI chat completions with tool-calling
3. Gradio custom Blocks interface
4. Dynamic ticket price lookup
5. DALL·E 3 image generation
6. TTS with OpenAI's speech API and pydub playback
"""

import os
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play
import gradio as gr

# ----------------------------
# 1. Setup Environment & Client
# ----------------------------
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"[INFO] OpenAI API Key loaded: {api_key[:8]}...")
else:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")

client = OpenAI(api_key=api_key)
MODEL = "gpt-4o"

# ----------------------------
# 2. System Prompt
# ----------------------------
system_message = (
    "You are a helpful assistant for an Airline called FlightAI. "
    "Give short, courteous answers. If a destination is discussed, generate an image and optionally speak the reply."
)

# ----------------------------
# 3. Tool Function (Flight Ticket Lookup)
# ----------------------------
ticket_prices = {
    "london": "$799",
    "paris": "$899",
    "tokyo": "$1400",
    "berlin": "$499"
}

def get_ticket_price(destination_city):
    city = destination_city.lower()
    print(f"[TOOL] Fetching price for: {city}")
    return ticket_prices.get(city, "Unknown")

price_tool = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city the customer wants to fly to."
            },
        },
        "required": ["destination_city"]
    }
}

tools = [{"type": "function", "function": price_tool}]

# ----------------------------
# 4. Tool Call Handler
# ----------------------------
def handle_tool_call(tool_call):
    args = json.loads(tool_call.function.arguments)
    city = args.get("destination_city", "").strip()
    price = get_ticket_price(city)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps({"destination_city": city, "price": price})
    }, city

# ----------------------------
# 5. Multimedia: Image Generation and TTS
# ----------------------------
def artist(city):
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in charcoal sketch style",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))

def talker(message):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=message
    )
    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)

# ----------------------------
# 6. Chat Function
# ----------------------------
def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    image = None
    city = None

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason == "tool_calls":
        tool_call = response.choices[0].message.tool_calls[0]
        tool_response, city = handle_tool_call(tool_call)

        tool_call_msg = response.choices[0].message
        tool_call_dict = {
            "role": str(tool_call_msg.role),
            "content": str(tool_call_msg.content or "")
        }
        if hasattr(tool_call_msg, "tool_calls"):
            tool_call_dict["tool_calls"] = tool_call_msg.tool_calls
        messages.append(tool_call_dict)
        messages.append(tool_response)

        if city:
            city = city.strip().lower()
            print(f"[DEBUG] Calling artist() with city: {city}")
            image = artist(city)

        response = client.chat.completions.create(model=MODEL, messages=messages)

    reply = response.choices[0].message.content
    if image and city:
        reply += f"\n\n🖼️ Here's a sketch of **{city.title()}**!"
    history.append({"role": "assistant", "content": reply})
    talker(reply)

    return history, image

# ----------------------------
# 7. Gradio UI
# ----------------------------
with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Ask FlightAI:")
    with gr.Row():
        clear = gr.Button("Clear")

    def do_entry(message, history):
        history.append({"role": "user", "content": message})
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: [], outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
