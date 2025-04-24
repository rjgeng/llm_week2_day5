import gradio as gr
import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ai_conversation(user_input):
    gpt_model = "gpt-4o-mini"
    claude_model = "claude-3-haiku-20240307"
    gpt_system = "You are a chatbot who is very argumentative; you challenge everything in a snarky way."
    claude_system = "You are a very polite chatbot who tries to agree and calm things down."

    gpt_msgs = [user_input]
    claude_msgs = ["Hi"]
    log = [f"User: {user_input}"]

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
        log.append(f"GPT: {gpt_reply}")
        log.append(f"Claude: {claude_reply}")

    return "\n\n".join(log)

# Gradio UI
demo = gr.Interface(
    fn=ai_conversation,
    inputs=gr.Textbox(label="Start the Conversation"),
    outputs=gr.Textbox(label="AI Conversation Log", lines=20),
    title="GPT-4o vs Claude-3-Haiku",
    description="Enter a message and watch GPT-4o-mini argue while Claude-3-Haiku calms things down!"
)

if __name__ == "__main__":
    demo.launch()
