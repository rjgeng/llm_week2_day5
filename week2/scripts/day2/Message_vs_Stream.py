import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Full Response Mode (non-streaming) ---
def get_full_response(user_message):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message}
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content

# --- Live Response Mode (streaming) ---
def get_live_response(user_message, chat_history):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for user_turn, ai_turn in chat_history:
        messages.append({"role": "user", "content": user_turn})
        messages.append({"role": "assistant", "content": ai_turn})
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    full_reply = ""
    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        full_reply += token
        yield full_reply

# --- Gradio App UI ---
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 GPT-4o-mini: Full vs Live Response")

    # Mode selector
    response_mode = gr.Radio(
        ["Full Response", "Live Response"],
        value="Full Response",
        label="Response Style",
        info="Choose how the AI should reply: all at once or in real-time"
    )

    # Full Response UI
    with gr.Column(visible=True) as full_response_ui:
        user_prompt = gr.Textbox(label="Your Message", placeholder="e.g. What's the capital of France?")
        ai_output = gr.Textbox(label="AI Reply", lines=8)
        send_btn = gr.Button("Send")
        send_btn.click(fn=get_full_response, inputs=user_prompt, outputs=ai_output)

    # Live Response UI (ChatInterface without invalid keys)
    with gr.Column(visible=False) as live_response_ui:
        chat = gr.ChatInterface(
            fn=get_live_response,
            title="Live Chat with GPT-4o-mini",
            description="Watch the AI respond in real-time, token by token."
        )

    # Toggle visibility based on selected mode
    def toggle_visibility(mode):
        return (
            gr.update(visible=(mode == "Full Response")),
            gr.update(visible=(mode == "Live Response")),
        )

    response_mode.change(
        fn=toggle_visibility,
        inputs=response_mode,
        outputs=[full_response_ui, live_response_ui]
    )

# Launch app
if __name__ == "__main__":
    demo.launch()
