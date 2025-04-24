import os
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai

import requests
from bs4 import BeautifulSoup
from typing import List

# ---------------------- Setup ----------------------
def setup_environment():
    load_dotenv(override=True)
    return {
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_key": os.getenv("GOOGLE_API_KEY"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
    }

key_list = setup_environment()

# ---------------------- Optional News Injection ----------------------
def fetch_headlines(url: str = "https://www.reuters.com/world/") -> List[str]:
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        headlines = [h3.get_text(strip=True) for h3 in soup.find_all("h3")][:5]
        return headlines or ["No headlines found."]
    except Exception as e:
        return [f"Failed to fetch news: {str(e)}"]

def append_news_if_applicable(system_prompt: str, personality: str) -> str:
    if personality.lower() in ["helpful", "motivational"]:
        headlines = fetch_headlines()
        news_block = "\n\n🗞️ Today's Headlines:\n" + "\n".join(f"- {line}" for line in headlines)
        return system_prompt + news_block
    return system_prompt

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

# ---------------------- Unified Interface ----------------------
def ask_model(user_input, provider_and_personality):
    provider, personality = provider_and_personality.split("::")

    system_prompt = "You are a helpful assistant."
    system_prompt = append_news_if_applicable(system_prompt, personality)

    messages = [
        {"role": "system", "content": system_prompt},
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
    else:
        return "❌ Unknown provider"

# ---------------------- Gradio UI ----------------------
providers = ["openai", "claude", "gemini", "deepseek"]
personalities = ["Neutral", "Helpful", "Motivational", "Snarky"]

combinations = [f"{p}::{pers}" for p in providers for pers in personalities]

view = gr.Interface(
    fn=ask_model,
    inputs=[
        gr.Textbox(label="Your message:", lines=6, placeholder="Ask anything..."),
        gr.Dropdown(combinations, label="Choose a model + personality", value="openai::Helpful")
    ],
    outputs=gr.Textbox(label="Response:", lines=8),
    title="🧠 Multi-Model AI Chat + News-Enhanced Personalities",
    description="Choose between GPT-4, Claude, Gemini, or DeepSeek. Personalities 'Helpful' & 'Motivational' get live news context."
)

# ---------------------- Main ----------------------
if __name__ == "__main__":
    # Console demo
    for combo in ["openai::Helpful", "claude::Neutral"]:
        print(f"\n=== {combo.upper()} ===")
        model, _ = combo.split("::")
        print(ask_model("What's happening in the world today?", combo))

    # Launch Gradio
    print("\n=== Chat UI ===\n")
    view.launch()
