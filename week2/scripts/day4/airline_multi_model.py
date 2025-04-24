"""
FlightAI Multi-Model Chatbot with Simulated Tool Calling
Supports: Ollama (local), OpenAI, Claude, Gemini, DeepSeek, Cohere
"""

import os
import re
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import google.generativeai as genai
import cohere


# ---------------------- Load API Keys ----------------------

def setup_environment():
    load_dotenv(override=True)
    return {
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_key": os.getenv("GOOGLE_API_KEY"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
        "cohere_key": os.getenv("COHERE_API_KEY")
    }


key_list = setup_environment()

# ---------------------- System Prompt ----------------------

SYSTEM_MESSAGE = """
You are a helpful assistant for an airline called FlightAI.
If a user asks about ticket prices, respond with this format:

TOOL:get_ticket_price("CityName")

Only use that format when the user asks about ticket cost or price. 
Otherwise, respond normally with short, polite answers.
"""

# ---------------------- Simulated Tool ----------------------

ticket_prices = {
    "london": "$799",
    "paris": "$899",
    "tokyo": "$1400",
    "berlin": "$499"
}


def get_ticket_price(city):
    city = city.lower()
    return ticket_prices.get(city, "Sorry, we don't have pricing info for that destination.")


TOOL_REGEX = r'TOOL:get_ticket_price\("([^\"]+)"\)'


def run_tool_if_needed(response_text):
    match = re.search(TOOL_REGEX, response_text)
    if match:
        city = match.group(1)
        price = get_ticket_price(city)
        return f"A return ticket to {city.title()} costs {price}."
    return response_text


# ---------------------- Model Wrappers ----------------------

def ask_openai(messages):
    client = OpenAI(api_key=key_list["openai_key"])
    response = client.chat.completions.create(model="gpt-4", messages=messages)
    return response.choices[0].message.content


def ask_claude(messages):
    client = anthropic.Anthropic(api_key=key_list["anthropic_key"])

    # Convert standard message format to Claude's format
    claude_messages = []
    system_content = ""

    # Extract system message first
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
            break

    # Add user/assistant messages
    for msg in messages:
        if msg["role"] != "system":
            # Only include role and content, no metadata
            claude_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        system=system_content,  # Pass system message separately
        messages=claude_messages
    )

    return response.content[0].text


def ask_gemini(messages):
    genai.configure(api_key=key_list["google_key"])
    system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
    history = [{"role": m["role"], "parts": [m["content"]]} for m in messages if m["role"] != "system"]
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp", system_instruction=system_prompt)
    chat = model.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    return response.text


def ask_deepseek(messages):
    client = OpenAI(api_key=key_list["deepseek_key"], base_url="https://api.deepseek.com")
    response = client.chat.completions.create(model="deepseek-chat", messages=messages)
    return response.choices[0].message.content


def ask_cohere(messages):
    client = cohere.Client(api_key=key_list["cohere_key"])

    # Map standard roles to Cohere's expected format
    role_mapping = {
        "user": "User",
        "assistant": "Chatbot",
        "system": "System"
    }

    # Get the latest user message
    user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

    # Format chat history for Cohere
    chat_history = []
    for i in range(len(messages) - 1):  # Skip the last message as it's handled separately
        m = messages[i]
        if m["role"] != "system":  # Skip system messages in history
            cohere_role = role_mapping.get(m["role"], "User")  # Default to User if unknown
            chat_history.append({"role": cohere_role, "message": m["content"]})

    response = client.chat(
        message=user_message,
        chat_history=chat_history,
        model="command-r-plus",
    )
    return response.text


def ask_ollama(messages):
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    response = client.chat.completions.create(model="llama3", messages=messages)
    return response.choices[0].message.content


# ---------------------- Dispatcher ----------------------

def multi_model_chat(user_input, history, provider):
    # Format history into messages
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}]

    # Convert Gradio history to message format
    for entry in history:
        if isinstance(entry, list) and len(entry) == 2:
            # Gradio history format: [user_message, assistant_message]
            if entry[0]:  # User message
                messages.append({"role": "user", "content": entry[0]})
            if entry[1]:  # Assistant message
                messages.append({"role": "assistant", "content": entry[1]})
        elif isinstance(entry, dict) and "role" in entry and "content" in entry:
            # Already in message format
            messages.append(entry)

    # Add current user input
    messages.append({"role": "user", "content": user_input})

    try:
        if provider == "openai":
            raw = ask_openai(messages)
        elif provider == "claude":
            raw = ask_claude(messages)
        elif provider == "gemini":
            raw = ask_gemini(messages)
        elif provider == "deepseek":
            raw = ask_deepseek(messages)
        elif provider == "cohere":
            raw = ask_cohere(messages)
        elif provider == "ollama":
            raw = ask_ollama(messages)
        else:
            return "❌ Unknown provider."

        return run_tool_if_needed(raw)
    except Exception as e:
        return f"Error: {str(e)}"


# ---------------------- Gradio UI ----------------------

def launch_interface():
    provider_dropdown = gr.Radio(
        choices=["openai", "claude", "gemini", "deepseek", "cohere", "ollama"],
        value="ollama",
        label="Select Model Provider",
        interactive=True
    )

    chatbot = gr.Chatbot(label="FlightAI", type="messages")

    def chat_wrapper(user_input, history, provider):
        return multi_model_chat(user_input, history, provider)

    gr.ChatInterface(
        fn=chat_wrapper,
        chatbot=chatbot,
        additional_inputs=[provider_dropdown],
        title="FlightAI: Multi-Model Airline Chatbot",
        description="Ask questions about flights, prices, or destinations. Ticket price inquiries trigger simulated tools.",
        type="messages"
    ).launch()


if __name__ == "__main__":
    launch_interface()