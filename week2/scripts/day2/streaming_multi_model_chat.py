import os
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai
import cohere  # ✅ Cohere import

# ---------------------- Load Keys ----------------------
def setup_environment():
    load_dotenv(override=True)
    return {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "deepseek": os.getenv("DEEPSEEK_API_KEY"),
        "cohere": os.getenv("COHERE_API_KEY")  # ✅ Add cohere
    }

key_list = setup_environment()
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ---------------------- Streaming Chat Logic ----------------------
def chat_stream(message, history, provider):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for user, assistant in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": message})

    if provider == "openai":
        client = OpenAI(api_key=key_list["openai"])
        reply = ""
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            yield reply

    elif provider == "deepseek":
        client = OpenAI(api_key=key_list["deepseek"], base_url=DEEPSEEK_BASE_URL)
        reply = ""
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            yield reply

    elif provider == "claude":
        client = anthropic.Anthropic(api_key=key_list["anthropic"])
        try:
            result = client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": message}],
                max_tokens=1000
            )
            yield result.content[0].text.strip()
        except Exception as e:
            yield f"❌ Claude error: {e}"

    elif provider == "gemini":
        genai.configure(api_key=key_list["google"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            chat = model.start_chat()
            response = chat.send_message(message)
            yield response.text
        except Exception as e:
            yield f"❌ Gemini error: {e}"

    elif provider == "cohere":  # ✅ Cohere integration
        client = cohere.Client(api_key=key_list["cohere"])
        try:
            reply = ""
            response = client.chat_stream(
                message=message,
                model="command-r-plus",
                temperature=0.7
            )
            for event in response:
                if event.event_type == "text-generation":
                    reply += event.text
                    yield reply
        except Exception as e:
            yield f"❌ Cohere error: {e}"

    else:
        yield "❌ Unknown provider."

# ---------------------- Gradio UI ----------------------
provider_selector = gr.Dropdown(
    choices=["openai", "claude", "gemini", "deepseek", "cohere"],  # ✅ added cohere
    label="Choose Model",
    value="openai"
)

demo = gr.ChatInterface(
    fn=chat_stream,
    additional_inputs=provider_selector,
    title="🧠 Simple Streaming Multi-Model Chat",
    description="Chat with GPT-4, Claude, Gemini, DeepSeek, or Cohere. GPT & DeepSeek stream live.",
)

# ---------------------- Launch ----------------------
if __name__ == "__main__":
    demo.launch(share=True)
