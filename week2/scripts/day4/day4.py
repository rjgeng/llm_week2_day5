"""
Pedagogical Demo: FlightAI Chatbot with Tool Calling using OpenAI and Gradio

This script demonstrates:
1. System prompt usage
2. OpenAI chat completions with tool-calling
3. Gradio ChatInterface integration
4. Dynamic ticket price lookup
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
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

MODEL = "gpt-4o-mini"
client = OpenAI(api_key=api_key)

# ----------------------------
# 2. System Prompt
# ----------------------------

system_message = (
    "You are a helpful assistant for an Airline called FlightAI. "
    "Give short, courteous answers, no more than 1 sentence. "
    "Always be accurate. If you don't know the answer, say so."
)

# ----------------------------
# 3. Tool Function
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

# Tool schema
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
    city = args.get("destination_city")
    price = get_ticket_price(city)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps({"destination_city": city, "price": price})
    }

# ----------------------------
# 5. Chat Function
# ----------------------------

def chat(user_input, history):
    messages = [{"role": "system", "content": system_message}]
    for h in history:
        if "role" in h and "content" in h:
            messages.append(h)
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason == "tool_calls":
        tool_call = response.choices[0].message.tool_calls[0]
        tool_response = handle_tool_call(tool_call)

        messages.append(response.choices[0].message)
        messages.append(tool_response)

        # Call again after tool response
        response = client.chat.completions.create(model=MODEL, messages=messages)

    return response.choices[0].message.content

# ----------------------------
# 6. Launch Gradio Interface
# ----------------------------

demo = gr.ChatInterface(fn=chat, type="messages")
demo.launch()
