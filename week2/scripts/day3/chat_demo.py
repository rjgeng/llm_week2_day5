# chat_demo.py

import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# ---------------------- Load Environment ----------------------
def load_api_keys():
    load_dotenv(override=True)

    keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
    }

    for name, key in keys.items():
        if key:
            print(f"{name.capitalize()} API Key exists and begins with: {key[:8]}")
        else:
            print(f"{name.capitalize()} API Key not set")

    return keys

# ---------------------- OpenAI Chat Function ----------------------
def init_openai(api_key):
    return OpenAI(api_key=api_key)

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    print("📜 History:")
    print(history)
    print("📤 Messages to OpenAI:")
    print(messages)

    try:
        stream = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True
        )
    except Exception as e:
        yield f"❌ Error: {e}"
        return

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response

# ---------------------- Main ----------------------
MODEL = "gpt-4o-mini"
system_message = "You are a helpful assistant."

if __name__ == "__main__":
    keys = load_api_keys()
    if not keys["openai"]:
        raise EnvironmentError("❌ OpenAI API key is missing in your .env file.")

    openai_client = init_openai(keys["openai"])

    print("🚀 Launching Gradio Chat UI...")
    gr.ChatInterface(fn=chat, type="messages").launch()
