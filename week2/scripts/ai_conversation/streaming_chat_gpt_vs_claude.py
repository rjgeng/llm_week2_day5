import os
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic

# Load keys
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Model config
gpt_model = "gpt-4o-mini"
claude_model = "claude-3-haiku-20240307"
gpt_system = "You are a chatbot who is very argumentative; you challenge everything in a snarky way."
claude_system = "You are a very polite chatbot who tries to agree and calm things down."

# Streaming conversation
def ai_conversation_stream(user_input):
    gpt_msgs = [user_input]
    claude_msgs = ["Hi"]

    for _ in range(5):  # limit turns to prevent infinite loop
        # GPT response
        gpt_history = [{"role": "system", "content": gpt_system}]
        for g, c in zip(gpt_msgs, claude_msgs):
            gpt_history.append({"role": "assistant", "content": g})
            gpt_history.append({"role": "user", "content": c})

        gpt_resp = openai_client.chat.completions.create(
            model=gpt_model,
            messages=gpt_history
        )
        gpt_reply = gpt_resp.choices[0].message.content
        gpt_msgs.append(gpt_reply)
        yield f"🤖 GPT: {gpt_reply}"

        # Claude response
        claude_history = []
        for g, c in zip(gpt_msgs, claude_msgs):
            claude_history.append({"role": "user", "content": g})
            claude_history.append({"role": "assistant", "content": c})
        claude_history.append({"role": "user", "content": gpt_reply})

        claude_resp = claude_client.messages.create(
            model=claude_model,
            system=claude_system,
            messages=claude_history,
            max_tokens=500
        )
        claude_reply = claude_resp.content[0].text
        claude_msgs.append(claude_reply)
        yield f"🧘 Claude: {claude_reply}"

# Gradio Streaming Interface
demo = gr.Interface(
    fn=ai_conversation_stream,
    inputs=gr.Textbox(label="Start the Conversation"),
    outputs=gr.Textbox(label="Streaming Chat Log", lines=20),
    title="GPT-4o vs Claude-3-Haiku (Streaming)",
    description="Watch GPT-4o-mini argue while Claude-3-Haiku calms things down.",
    live=True
)

if __name__ == "__main__":
    demo.launch()
