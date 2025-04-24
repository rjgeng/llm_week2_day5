import os
import time
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from typing import List

# -------------------- Setup --------------------
load_dotenv()
KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "google": os.getenv("GOOGLE_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_API_KEY"),
}
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# -------------------- Personalities + News --------------------
def fetch_headlines(url="https://www.reuters.com/world/") -> List[str]:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        return [h.get_text(strip=True) for h in soup.find_all("h3")][:5]
    except Exception as e:
        return [f"❌ Failed to fetch news: {e}"]

def inject_news(system_prompt: str, personality: str) -> str:
    if personality.lower() in ["helpful", "motivational"]:
        headlines = fetch_headlines()
        news_block = "\n\n🗞️ Today's Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
        return system_prompt + news_block
    return system_prompt

# -------------------- Model Router --------------------
def stream_response(message, history, model_choice):
    provider, personality = model_choice.split("::")
    system_prompt = inject_news("You are a helpful assistant.", personality)

    # Build messages list
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})

    if provider == "openai":
        client = OpenAI(api_key=KEYS["openai"])
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True
        )
        reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            yield reply

    elif provider == "deepseek":
        client = OpenAI(api_key=KEYS["deepseek"], base_url=DEEPSEEK_BASE_URL)
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True
        )
        reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            yield reply

    elif provider == "claude":
        client = anthropic.Anthropic(api_key=KEYS["anthropic"])
        filtered = [m for m in messages if m["role"] != "system"]
        try:
            result = client.messages.create(
                model="claude-3-haiku-20240307",
                messages=filtered,
                max_tokens=1000
            )
            yield result.content[0].text.strip()
        except Exception as e:
            yield f"❌ Claude error: {e}"

    elif provider == "gemini":
        genai.configure(api_key=KEYS["google"])
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        history_gen = [{"role": m["role"], "parts": [m["content"]]} for m in messages if m["role"] != "system"]
        model = genai.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=history_gen)
        try:
            response = chat.send_message(message)
            yield response.text
        except Exception as e:
            yield f"❌ Gemini error: {e}"

    else:
        yield "❌ Unknown model provider."

# -------------------- UI --------------------
model_options = [f"{p}::{tone}" for p in ["openai", "claude", "gemini", "deepseek"]
                 for tone in ["Neutral", "Helpful", "Motivational", "Snarky"]]

demo = gr.ChatInterface(
    fn=stream_response,
    additional_inputs=gr.Dropdown(model_options, label="Choose Model + Personality", value="openai::Helpful"),
    title="🧠 Multi-Model AI Chat (Streaming)",
    description="Talk to GPT-4, Claude, Gemini, or DeepSeek with different personalities. 'Helpful' and 'Motivational' inject live news 🗞️"
)

if __name__ == "__main__":
    demo.launch(share=True)
