# deepseek_only.py

import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import display, Markdown
import builtins

# ---------------------- Setup ----------------------
def setup_environment():
    load_dotenv(override=True)
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return {
        "output_path": os.path.join("output", f"deepseek_{timestamp}.md"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
    }

# ---------------------- Output Helper ----------------------
outputs = []

def record_output(model_name, content):
    print(f"\n🤖 {model_name}:\n{content}")
    outputs.append(f"## {model_name}\n\n{content.strip()}\n\n")

# ---------------------- DeepSeek Generation ----------------------
def run_deepseek(keys):
    prompts = [
        {"role": "system", "content": "You are an assistant that is great at telling jokes"},
        {"role": "user", "content": "Tell a light-hearted joke for an audience of Data Scientists"}
    ]

    if keys["deepseek_key"]:
        try:
            deepseek = OpenAI(api_key=keys["deepseek_key"], base_url="https://api.deepseek.com")
            response = deepseek.chat.completions.create(model="deepseek-chat", messages=prompts)
            record_output("DeepSeek Chat", response.choices[0].message.content)
        except Exception as e:
            record_output("DeepSeek Chat", f"⚠️ Error: {e}")
    else:
        print("\n⚠️ Skipping DeepSeek – API key not set.")

# ---------------------- DeepSeek Advanced ----------------------
def in_ipython():
    try:
        return getattr(builtins, '__IPYTHON__', False)
    except NameError:
        return False

def deepseek_advanced(keys):
    if not keys["deepseek_key"]:
        print("\n⚠️ Skipping DeepSeek advanced section – API key not set.")
        return

    deepseek = OpenAI(api_key=keys["deepseek_key"], base_url="https://api.deepseek.com")
    challenge_prompt = [
        {"role": "system", "content": "You are an expert reasoning assistant."},
        {"role": "user", "content": "Explain why the sky is blue in terms a 10-year-old can understand."}
    ]

    try:
        print("\n🤖 DeepSeek Chat (streaming response):\n")
        reply = ""
        display_handle = display(Markdown(""), display_id=True) if in_ipython() else None

        stream = deepseek.chat.completions.create(model="deepseek-chat", messages=challenge_prompt, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            reply += delta
            if display_handle:
                display_handle.update(Markdown(reply.replace("```", "").replace("markdown", "")))
            else:
                print(delta, end="", flush=True)

        print("\n\n🔢 Number of words:", len(reply.split()))
    except Exception as e:
        print(f"⚠️ Streaming error with DeepSeek Chat: {e}")

    try:
        print("\n🤖 DeepSeek Reasoner:\n")
        response = deepseek.chat.completions.create(model="deepseek-reasoner", messages=challenge_prompt)
        msg = response.choices[0].message
        reasoning = getattr(msg, "reasoning_content", "(no reasoning provided)")
        print("🔍 Reasoning:\n", reasoning)
        print("\n💬 Answer:\n", msg.content)
        print("\n🔢 Number of words:", len(msg.content.split()))
    except Exception as e:
        print(f"⚠️ DeepSeek Reasoner error: {e}")

# ---------------------- Save ----------------------
def save_to_file(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# DeepSeek Model Output\n\n")
        f.writelines(outputs)
    print(f"\n✅ Output saved to: {path}")

# ---------------------- Main ----------------------
if __name__ == "__main__":
    keys = setup_environment()
    run_deepseek(keys)
    deepseek_advanced(keys)
    save_to_file(keys["output_path"])
