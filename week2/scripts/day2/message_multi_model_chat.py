import os
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai
import cohere  # ✅ Added for Cohere support

# ---------------------- Setup ----------------------
def setup_environment():
    load_dotenv(override=True)
    return {
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_key": os.getenv("GOOGLE_API_KEY"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
        "cohere_key": os.getenv("COHERE_API_KEY")  # ✅ Add Cohere key
    }

key_list = setup_environment()

# ---------------------- Model Wrappers ----------------------

def ask_gpt(messages):
    client = OpenAI(api_key=key_list["openai_key"])
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content

def ask_claude(messages):
    client = anthropic.Anthropic(api_key=key_list["anthropic_key"])
    filtered = [m for m in messages if m["role"] != "system"]
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=filtered
    )
    return response.content[0].text

def ask_gemini(messages):
    genai.configure(api_key=key_list["google_key"])
    system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
    history = [{"role": m["role"], "parts": [m["content"]]} for m in messages if m["role"] != "system"]
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=system_prompt
    )
    chat = model.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    return response.text

def ask_deepseek(messages):
    client = OpenAI(api_key=key_list["deepseek_key"], base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content

def ask_cohere(messages):
    client = cohere.Client(api_key=key_list["cohere_key"])
    filtered = [m for m in messages if m["role"] != "system"]
    response = client.chat(
        message=filtered[-1]["content"],
        chat_history=[{"role": m["role"], "message": m["content"]} for m in filtered[:-1]],
        model="command-r-plus",  # or use "command-r"
    )
    return response.text

# ---------------------- Unified Interface ----------------------
def ask_model(user_input, provider):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]

    if provider == "openai":
        return ask_gpt(messages)
    elif provider == "claude":
        return ask_claude(messages)
    elif provider == "gemini":
        return ask_gemini(messages)
    elif provider == "deepseek":
        return ask_deepseek(messages)
    elif provider == "cohere":
        return ask_cohere(messages)
    else:
        return "❌ Unknown provider"

# ---------------------- Gradio UI ----------------------
view = gr.Interface(
    fn=ask_model,
    inputs=[
        gr.Textbox(label="Your message:", lines=6, placeholder="Ask anything..."),
        gr.Radio(["openai", "claude", "gemini", "deepseek", "cohere"], label="Choose a model")  # ✅ Added cohere
    ],
    outputs=gr.Textbox(label="Response:", lines=8),
    title="Multi-Model AI Chat Interface",
    description="Choose between GPT-4, Claude, Gemini, DeepSeek, or Cohere."
)

# ---------------------- Main ----------------------
if __name__ == "__main__":
    for provider in ["openai", "claude", "gemini", "deepseek", "cohere"]:
        print(f"\n=== {provider.upper()} ===")
        print(ask_model("Who made you?", provider))

    print("\n=== Chat UI ===\n")
    view.launch()
