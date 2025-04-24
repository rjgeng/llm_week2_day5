import os
from datetime import datetime
import gradio as gr
import anthropic
from openai import OpenAI
from dotenv import load_dotenv

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Validate DeepSeek Key ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("❌ Missing DEEPSEEK_API_KEY. Export it or add it to your .env file.")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ---------- Claude Setup ----------
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
if not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError("❌ Missing ANTHROPIC_API_KEY. Export it or add it to your .env file.")

# ---------- Personality Profiles ----------
PERSONALITIES = {
    "Polite": "You are a very polite chatbot who tries to agree and calm things down.",
    "Snarky": "You are a chatbot who is very argumentative; you challenge everything in a snarky way.",
    "Helpful": "You are a helpful assistant that gives concise and accurate answers.",
    "Motivational": "You are a highly energetic motivational coach who inspires confidence."
}

# ---------- Save Markdown Output ----------
def save_convo(convo):
    os.makedirs("output", exist_ok=True)
    filename = f"output/claude_vs_deepseek_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Claude 😇 vs DeepSeek 😈 Conversation\n\n")
        for speaker, msg in convo:
            role = "User" if speaker is None else speaker
            f.write(f"**{role}:** {msg}\n\n")
    print(f"💾 Saved to {filename}")

# ---------- DeepSeek Initialization ----------
def init_deepseek():
    print("🔑 Using DeepSeek Key:", DEEPSEEK_API_KEY[:10] + "...")
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    # Optional ping to confirm key validity
    _ = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1
    )
    return client

# ---------- Main Conversation Simulation ----------
def simulate_convo(user_input, turns, claude_personality, deepseek_personality, deepseek_model):
    try:
        deepseek = init_deepseek()
    except Exception as e:
        return [{"role": "user", "content": f"❌ DeepSeek Init Error: {e}"}]

    convo = [(None, user_input)]
    claude_msgs = [("User", user_input)]
    deepseek_msgs = ["Hi"]

    def call_claude():
        messages = []
        for u, c in zip(deepseek_msgs, [m[1] for m in claude_msgs]):
            messages.append({"role": "user", "content": u})
            messages.append({"role": "assistant", "content": c})
        messages.append({"role": "user", "content": deepseek_msgs[-1]})
        try:
            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                system=PERSONALITIES[claude_personality],
                messages=messages,
                max_tokens=512
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"⚠️ Claude Error: {e}"

    def call_deepseek():
        messages = [{"role": "system", "content": PERSONALITIES[deepseek_personality]}]
        for c in claude_msgs:
            messages.append({"role": "assistant", "content": c[1]})
        for d in deepseek_msgs:
            messages.append({"role": "user", "content": d})
        try:
            response = deepseek.chat.completions.create(
                model=deepseek_model,
                messages=messages,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ DeepSeek Error: {e}"

    for _ in range(turns):
        claude_reply = call_claude()
        deepseek_reply = call_deepseek()

        claude_msgs.append(("Claude 😇", claude_reply))
        deepseek_msgs.append(deepseek_reply)

        convo.append(("Claude 😇", claude_reply))
        convo.append(("DeepSeek 😈", deepseek_reply))

    save_convo(convo)

    return [{"role": "user" if speaker is None else "assistant", "content": f"{speaker or 'User'}: {msg}"} for speaker, msg in convo]

# ---------- Gradio UI ----------
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Claude vs DeepSeek – AI Personality Battle")

    with gr.Row():
        user_input = gr.Textbox(label="Start Message", placeholder="Say something...", lines=2)
        deepseek_model = gr.Dropdown(["deepseek-chat", "deepseek-reasoner"], label="DeepSeek Model", value="deepseek-chat")
        claude_p = gr.Dropdown(choices=list(PERSONALITIES.keys()), label="Claude Personality", value="Helpful")
        deepseek_p = gr.Dropdown(choices=list(PERSONALITIES.keys()), label="DeepSeek Personality", value="Snarky")
        turn_slider = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Conversation Turns")
        run_btn = gr.Button("Run Showdown")

    chat_ui = gr.Chatbot(label="Conversation Log", height=600, type="messages")

    run_btn.click(
        fn=simulate_convo,
        inputs=[user_input, turn_slider, claude_p, deepseek_p, deepseek_model],
        outputs=chat_ui
    )

if __name__ == "__main__":
    demo.launch(share=True)
