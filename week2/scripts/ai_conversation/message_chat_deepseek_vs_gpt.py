import os
from datetime import datetime
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

# ---------- Output Directory ----------
os.makedirs("output", exist_ok=True)

# ---------- Personalities ----------
PERSONALITIES = {
    "Polite": "You are a very polite chatbot who tries to agree and calm things down.",
    "Snarky": "You are a chatbot who is very argumentative; you challenge everything in a snarky way.",
    "Helpful": "You are a helpful assistant that gives concise and accurate answers.",
    "Motivational": "You are a highly energetic motivational coach who inspires confidence."
}

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Validate DeepSeek Key ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("❌ Missing DEEPSEEK_API_KEY. Export it or add it to your .env file.")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

def get_clients():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    print("✅ DeepSeek API Key used:", DEEPSEEK_API_KEY[:10] + "...")
    return openai_client, deepseek_client

# ---------- Conversation Helpers ----------
def build_message_history(gpt_msgs, deepseek_msgs, system_prompt, is_gpt):
    messages = [{"role": "system", "content": system_prompt}]
    if is_gpt:
        for g, d in zip(gpt_msgs, deepseek_msgs):
            messages.append({"role": "assistant", "content": g})
            messages.append({"role": "user", "content": d})
    else:
        for g, d in zip(gpt_msgs, deepseek_msgs):
            messages.append({"role": "user", "content": g})
            messages.append({"role": "assistant", "content": d})
        messages.append({"role": "user", "content": gpt_msgs[-1]})
    return messages

def simulate_convo(user_input, gpt_model, deepseek_model, num_turns, gpt_personality, deepseek_personality):
    openai_client, deepseek_client = get_clients()

    gpt_system = PERSONALITIES[gpt_personality]
    deepseek_system = PERSONALITIES[deepseek_personality]

    gpt_msgs = [user_input]
    deepseek_msgs = ["Hi"]
    convo = [("User", user_input)]

    for _ in range(num_turns):
        # GPT response
        gpt_messages = build_message_history(gpt_msgs, deepseek_msgs, gpt_system, is_gpt=True)
        gpt_reply = openai_client.chat.completions.create(
            model=gpt_model,
            messages=gpt_messages
        ).choices[0].message.content.strip()
        gpt_msgs.append(gpt_reply)
        convo.append((f"{gpt_model} ({gpt_personality})", gpt_reply))

        # DeepSeek response
        deepseek_messages = build_message_history(gpt_msgs, deepseek_msgs, deepseek_system, is_gpt=False)
        deepseek_reply = deepseek_client.chat.completions.create(
            model=deepseek_model,
            messages=deepseek_messages,
            max_tokens=500
        ).choices[0].message.content.strip()
        deepseek_msgs.append(deepseek_reply)
        convo.append((f"{deepseek_model} ({deepseek_personality})", deepseek_reply))

    save_conversation(convo, (gpt_model, deepseek_model))
    return convo

# ---------- Save Markdown Output ----------
def save_conversation(convo, model_names):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"output/convo_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {model_names[0]} vs {model_names[1]} Conversation\n\n")
        for speaker, message in convo:
            f.write(f"**{speaker}:** {message}\n\n")
    print(f"💾 Chat saved to {filename}")

# ---------- Gradio UI ----------
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 GPT 😈 vs DeepSeek 😇 — AI Personality Clash")

    with gr.Row():
        user_input = gr.Textbox(label="Your Message", placeholder="Start the chat", lines=2)
        gpt_selector = gr.Dropdown(label="GPT Model", choices=["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"], value="gpt-4o-mini")
        deepseek_selector = gr.Dropdown(label="DeepSeek Model", choices=["deepseek-chat", "deepseek-reasoner"], value="deepseek-chat")
        gpt_personality_selector = gr.Dropdown(label="GPT Personality", choices=list(PERSONALITIES.keys()), value="Snarky")
        deepseek_personality_selector = gr.Dropdown(label="DeepSeek Personality", choices=list(PERSONALITIES.keys()), value="Polite")
        turn_slider = gr.Slider(label="Conversation Turns", minimum=1, maximum=10, value=5, step=1)
        launch_btn = gr.Button("Run Showdown")

    chat_ui = gr.Chatbot(label="Chat Log", height=600, type='messages')

    def run_chat(message, gpt_model, deepseek_model, turns, gpt_personality, deepseek_personality):
        convo = simulate_convo(message, gpt_model, deepseek_model, turns, gpt_personality, deepseek_personality)
        ui_convo = []
        for speaker, reply in convo:
            if speaker == "User":
                ui_convo.append({"role": "user", "content": f"🧑‍💬 {speaker}: {reply}"})
            else:
                ui_convo.append({"role": "assistant", "content": f"🤖 {speaker}: {reply}"})
        return ui_convo

    launch_btn.click(
        fn=run_chat,
        inputs=[user_input, gpt_selector, deepseek_selector, turn_slider, gpt_personality_selector, deepseek_personality_selector],
        outputs=chat_ui
    )

if __name__ == "__main__":
    demo.launch(share=True)
