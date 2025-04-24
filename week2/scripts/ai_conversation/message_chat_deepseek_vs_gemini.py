import os
from datetime import datetime
import gradio as gr
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Validate DeepSeek Key ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("❌ Missing DEEPSEEK_API_KEY. Export it or add it to your .env file.")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ✅ Gemini setup (uses GOOGLE_API_KEY if present)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ✅ DeepSeek initialization (validated key)
def init_deepseek():
    print("🔑 Using DeepSeek Key:", DEEPSEEK_API_KEY)
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    # Optional ping
    _ = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1
    )
    return client

# ✅ Markdown saving
def save_convo(convo):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output", exist_ok=True)
    path = f"output/test_gemini_vs_deepseek_{timestamp}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Gemini 😇 vs DeepSeek 😈 Conversation\n\n")
        for speaker, msg in convo:
            if speaker is None:
                f.write(f"**User:** {msg}\n\n")
            else:
                f.write(f"**{speaker}:** {msg}\n\n")
    print(f"💾 Saved to {path}")

# ✅ Conversation logic
def simulate_convo(user_input):
    try:
        deepseek = init_deepseek()
    except Exception as e:
        return [(None, f"❌ DeepSeek init error: {e}")]

    gemini_msgs = [user_input]
    deepseek_msgs = ["Hi"]
    convo = [(None, f"User: {user_input}")]

    def call_gemini():
        history = [{"role": "user", "parts": [user_input]}]
        for g, d in zip(gemini_msgs, deepseek_msgs):
            history.append({"role": "model", "parts": [g]})
            history.append({"role": "user", "parts": [d]})
        return gemini_model.generate_content(history).text.strip()

    def call_deepseek():
        messages = [{"role": "system", "content": "You are sarcastic and love arguing."}]
        for g, d in zip(gemini_msgs, deepseek_msgs):
            messages.append({"role": "assistant", "content": g})
            messages.append({"role": "user", "content": d})
        reply = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=300
        )
        return reply.choices[0].message.content.strip()

    for _ in range(5):
        try:
            g_reply = call_gemini()
        except Exception as e:
            g_reply = f"⚠️ Gemini error: {e}"

        try:
            d_reply = call_deepseek()
        except Exception as e:
            d_reply = f"⚠️ DeepSeek error: {e}"

        gemini_msgs.append(g_reply)
        deepseek_msgs.append(d_reply)

        convo.append(("Gemini 😇", g_reply))
        convo.append(("DeepSeek 😈", d_reply))

    save_convo(convo)
    return convo

# ✅ Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Gemini vs DeepSeek – Personality Battle")
    user_input = gr.Textbox(label="Start Message", placeholder="Say something...", lines=2)
    run_btn = gr.Button("Start Conversation")
    chatbox = gr.Chatbot(label="Conversation", height=600)

    run_btn.click(fn=simulate_convo, inputs=user_input, outputs=chatbox)

# ✅ Launch
if __name__ == "__main__":
    demo.launch(share=True)
