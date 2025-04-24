# ai_conversation_demo.py

import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import anthropic

# Setup
def setup_environment():
    load_dotenv(override=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("output", exist_ok=True)
    return {
        "output_path": f"output/conversation_{timestamp}.md",
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
    }

# Run conversation between GPT-4o-mini and Claude-3-Haiku
def run_conversation(openai_client, claude_client):
    gpt_model = "gpt-4o-mini"
    claude_model = "claude-3-haiku-20240307"

    gpt_system = "You are a chatbot who is very argumentative; you challenge everything in a snarky way."
    claude_system = "You are a very polite chatbot who tries to agree and calm things down."

    gpt_msgs = ["Hi there"]
    claude_msgs = ["Hi"]
    conversation_log = []

    def call_gpt():
        messages = [{"role": "system", "content": gpt_system}]
        for g, c in zip(gpt_msgs, claude_msgs):
            messages.append({"role": "assistant", "content": g})
            messages.append({"role": "user", "content": c})
        reply = openai_client.chat.completions.create(model=gpt_model, messages=messages)
        return reply.choices[0].message.content

    def call_claude():
        messages = []
        for g, c in zip(gpt_msgs, claude_msgs):
            messages.append({"role": "user", "content": g})
            messages.append({"role": "assistant", "content": c})
        messages.append({"role": "user", "content": gpt_msgs[-1]})
        reply = claude_client.messages.create(
            model=claude_model,
            system=claude_system,
            messages=messages,
            max_tokens=500
        )
        return reply.content[0].text

    for _ in range(5):
        gpt_reply = call_gpt()
        claude_reply = call_claude()
        gpt_msgs.append(gpt_reply)
        claude_msgs.append(claude_reply)

        print(f"\nGPT: {gpt_reply}")
        print(f"Claude: {claude_reply}")
        conversation_log.append(f"**GPT**: {gpt_reply}\n\n**Claude**: {claude_reply}\n\n")

    return conversation_log

# Save to file
def save_conversation(log, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# GPT-4o-mini vs Claude-3-Haiku Conversation\n\n")
        f.writelines(log)
    print(f"\n✅ Saved to {path}")

# Main
if __name__ == "__main__":
    keys = setup_environment()
    openai_client = OpenAI(api_key=keys["openai_key"])
    claude_client = anthropic.Anthropic(api_key=keys["anthropic_key"])
    log = run_conversation(openai_client, claude_client)
    save_conversation(log, keys["output_path"])
