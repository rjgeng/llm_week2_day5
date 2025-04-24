import gradio as gr
import requests
import json

def chat_with_llama(message, history):
    # Start with the latest user message
    messages = [{"role": "user", "content": message}]

    # Safely extract from history
    if history:
        for pair in reversed(history):
            try:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    user_msg, assistant_msg = pair
                    if isinstance(user_msg, dict) and isinstance(assistant_msg, dict):
                        messages.insert(0, {"role": "assistant", "content": assistant_msg.get("content", "")})
                        messages.insert(0, {"role": "user", "content": user_msg.get("content", "")})
            except Exception as e:
                print(f"⚠️ Skipping malformed history item: {pair} ({e})")

    # Send request to Ollama
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "llama3", "messages": messages, "stream": True},
            stream=True
        )
    except Exception as e:
        yield f"❌ Could not connect to Ollama: {e}"
        return

    # Stream tokens
    partial = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.lstrip(b"data: ").decode("utf-8"))
                token = data.get("message", {}).get("content", "")
                partial += token
                yield partial
            except Exception as e:
                yield f"\n❌ Error in stream parsing: {e}"
                break

# Run Gradio UI
if __name__ == "__main__":
    gr.ChatInterface(
        fn=chat_with_llama,
        type="messages",
        title="🦙 LLaMA 3 Chatbot (Ollama)",
        theme="default"
    ).launch()
