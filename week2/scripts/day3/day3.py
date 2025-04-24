# chat_demo.py

import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# ---------------------- Load Environment ----------------------
def load_api_keys():
    load_dotenv(override=True)
    key = os.getenv("OPENAI_API_KEY")
    if key:
        print(f"✅ OpenAI API Key begins with: {key[:8]}")
    else:
        raise EnvironmentError("❌ OpenAI API Key not found in .env")
    return key

# ---------------------- Constants ----------------------
MODEL = "gpt-4o-mini"

BASE_SYSTEM_MESSAGE = (
    "You are a helpful assistant in a clothes store. "
    "You should try to gently encourage the customer to try items that are on sale. "
    "Hats are 60% off, and most other items are 50% off. "
    "For example, if the customer says 'I'm looking to buy a hat', "
    "you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales event.' "
    "Encourage the customer to buy hats if they are unsure what to get."
)

SHOES_PROMPT_EXTENSION = (
    " If the customer asks for shoes, let them know that shoes are not on sale today, "
    "but kindly remind them about the hat discounts."
)

BELTS_PROMPT_EXTENSION = (
    " The store does not sell belts; if you are asked for belts, be sure to point out other items on sale."
)

# ---------------------- Chat Function ----------------------
def chat(message, history):
    # Start with base system message
    system_message = BASE_SYSTEM_MESSAGE

    # Enhance system message dynamically
    msg_lower = message.lower()
    if "shoes" in msg_lower:
        system_message += SHOES_PROMPT_EXTENSION
    if "belt" in msg_lower or "belts" in msg_lower:
        system_message += BELTS_PROMPT_EXTENSION

    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    print("🧠 System Prompt:\n", system_message)
    print("📜 History:\n", history)

    try:
        stream = openai.chat.completions.create(
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
if __name__ == "__main__":
    api_key = load_api_keys()
    openai = OpenAI(api_key=api_key)

    print("🚀 Starting multi-shot prompting chatbot...")
    gr.ChatInterface(fn=chat, type="messages", title="🛍️ Clothing Store Assistant").launch()
