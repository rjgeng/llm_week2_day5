import os
from datetime import datetime
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

# ---------- Setup ----------
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not DEEPSEEK_API_KEY or not OPENAI_KEY:
    raise RuntimeError("❌ API key(s) missing. Check .env")

os.makedirs("output", exist_ok=True)

PERSONALITIES = {
    "Polite": "You are a very polite chatbot who tries to agree and calm things down.",
    "Snarky": "You are a chatbot who is very argumentative; you challenge everything in a snarky way.",
    "Helpful": "You are a helpful assistant that gives concise and accurate answers.",
    "Motivational": "You are a highly energetic motivational coach who inspires confidence."
}

# ---------- Helper ----------
def build_history(gpt_msgs, deepseek_msgs, system_msg, is_gpt=True):
    messages = [{"role": "system", "content": system_msg}]
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

# ---------- Streaming Function ----------
def run_chat_stream(message, history):
    gpt_model = "gpt-4o-mini"
    deepseek_model = "deepseek-chat"
    gpt_personality = "Snarky"
    deepseek_personality = "Polite"
    num_turns = 5

    openai_client = OpenAI(api_key=OPENAI_KEY)
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    gpt_msgs = [message]
    deepseek_msgs = ["Hi"]
    convo_log = [("User", message)]

    yield "🧑‍💬 User: " + message

    for _ in range(num_turns):
        # GPT streams first
        gpt_response = ""
        stream = openai_client.chat.completions.create(
            model=gpt_model,
            messages=build_history(gpt_msgs, deepseek_msgs, PERSONALITIES[gpt_personality], is_gpt=True),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            gpt_response += delta
            yield f"🤖 {gpt_model} ({gpt_personality}): {gpt_response}"
        gpt_msgs.append(gpt_response)
        convo_log.append((f"{gpt_model} ({gpt_personality})", gpt_response))

        # DeepSeek streams back
        deepseek_response = ""
        stream = deepseek_client.chat.completions.create(
            model=deepseek_model,
            messages=build_history(gpt_msgs, deepseek_msgs, PERSONALITIES[deepseek_personality], is_gpt=False),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            deepseek_response += delta
            yield f"🤖 {deepseek_model} ({deepseek_personality}): {deepseek_response}"
        deepseek_msgs.append(deepseek_response)
        convo_log.append((f"{deepseek_model} ({deepseek_personality})", deepseek_response))

    save_conversation(convo_log, gpt_model, deepseek_model)

# ---------- Markdown Output ----------
def save_conversation(convo, gpt_model, deepseek_model):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"output/convo_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {gpt_model} vs {deepseek_model} Chat\n\n")
        for speaker, msg in convo:
            f.write(f"**{speaker}:** {msg.strip()}\n\n")
    print(f"💾 Conversation saved to {filename}")

# ---------- Launch UI ----------
demo = gr.ChatInterface(
    fn=run_chat_stream,
    title="🤖 GPT vs DeepSeek – Streaming AI Personality Showdown",
    description="Enter a message. Watch GPT-4o (Snarky) and DeepSeek (Polite) go back and forth for 5 turns.",
)

if __name__ == "__main__":
    demo.launch(share=True)
