import os
import re
import gradio as gr
from openai import OpenAI

# ----------------------------
# 1. Setup Ollama Client
# ----------------------------

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL = "llama3"

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # Dummy, not used by Ollama
)

# ----------------------------
# 2. System Prompt (tell it to simulate tools)
# ----------------------------

system_message = """
You are a helpful assistant for an airline called FlightAI.
If a user asks about ticket prices, respond with this format:

TOOL:get_ticket_price("CityName")

Only use that format when the user asks about ticket cost or price. 
For all other questions, respond normally with short, polite answers.
"""

# ----------------------------
# 3. Simulated Tool Function
# ----------------------------

ticket_prices = {
    "london": "$799",
    "paris": "$899",
    "tokyo": "$1400",
    "berlin": "$499"
}

def get_ticket_price(city):
    city = city.lower()
    print(f"[TOOL] Called for: {city}")
    return ticket_prices.get(city, "Sorry, we don't have pricing info for that destination.")

# ----------------------------
# 4. Chat Function with Tool Simulation
# ----------------------------

TOOL_REGEX = r'TOOL:get_ticket_price\("([^"]+)"\)'

def chat(user_input, history):
    messages = [{"role": "system", "content": system_message}]
    for h in history:
        if "role" in h and "content" in h:
            messages.append(h)
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )

    output = response.choices[0].message.content

    # Check for simulated tool call pattern
    match = re.search(TOOL_REGEX, output)
    if match:
        city = match.group(1)
        price = get_ticket_price(city)
        return f"A return ticket to {city.title()} costs {price}."
    else:
        return output

# ----------------------------
# 5. Launch Gradio Chat UI
# ----------------------------

gr.ChatInterface(fn=chat, type="messages").launch()
