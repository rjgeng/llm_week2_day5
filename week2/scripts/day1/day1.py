# day1.py

import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import google.generativeai
from IPython.display import display, Markdown
import builtins

# ---------------------- Setup ----------------------
def setup_environment():
    load_dotenv(override=True)
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return {
        "output_path": os.path.join("output", f"jokes_{timestamp}.md"),
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_key": os.getenv("GOOGLE_API_KEY"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
    }

# ---------------------- Display API Keys ----------------------
def check_api_keys(keys):
    print("\n🔐 API Key Check:")
    for name, key in keys.items():
        if name.endswith("_key"):
            provider = name.replace("_key", "").capitalize()
            print(f"✅ {provider} Key: {'Found' if key else 'Not found'}")

# ---------------------- Output Helper ----------------------
outputs = []

def record_output(model_name, content):
    print(f"\n🤖 {model_name}:\n{content}")
    outputs.append(f"## {model_name}\n\n{content.strip()}\n\n")

# ---------------------- Generate Jokes ----------------------
def generate_model_jokes(keys):
    system_msg = "You are an assistant that is great at telling jokes"
    user_msg = "Tell a light-hearted joke for an audience of Data Scientists"
    prompts = [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
    
    openai_client = OpenAI()
    claude_client = anthropic.Anthropic()
    google.generativeai.configure(api_key=keys["google_key"])

    for model, temp in [("gpt-3.5-turbo", 0.7), ("gpt-4o-mini", 0.7), ("gpt-4o", 0.4)]:
        response = openai_client.chat.completions.create(model=model, messages=prompts, temperature=temp)
        record_output(model.replace("-", " ").title(), response.choices[0].message.content)

    claude_response = claude_client.messages.create(
        model="claude-3-5-sonnet-latest",
        system=system_msg,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=200,
        temperature=0.7
    )
    record_output("Claude 3.5 Sonnet", claude_response.content[0].text)

    stream_text = ""
    print("\n🤖 Claude 3.5 Sonnet (streaming):")
    with claude_client.messages.stream(
        model="claude-3-5-sonnet-latest",
        system=system_msg,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=200,
        temperature=0.7
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta":
                delta = event.delta.text
                print(delta, end="", flush=True)
                stream_text += delta
    record_output("Claude 3.5 Sonnet (Streaming)", stream_text)

    gemini_sdk = google.generativeai.GenerativeModel(
        model_name="gemini-2.0-flash-exp", system_instruction=system_msg
    )
    response = gemini_sdk.generate_content(user_msg)
    record_output("Gemini 2.0 (via SDK)", response.text)

    gemini_openai = OpenAI(
        api_key=keys["google_key"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = gemini_openai.chat.completions.create(
        model="gemini-2.0-flash-exp", messages=prompts
    )
    record_output("Gemini 2.0 (OpenAI-Compatible)", response.choices[0].message.content)

    if keys["deepseek_key"]:
        try:
            deepseek = OpenAI(api_key=keys["deepseek_key"], base_url="https://api.deepseek.com")
            response = deepseek.chat.completions.create(model="deepseek-chat", messages=prompts)
            record_output("DeepSeek Chat", response.choices[0].message.content)
        except Exception as e:
            record_output("DeepSeek Chat", f"⚠️ Error: {e}")
    else:
        print("\n⚠️ Skipping DeepSeek – API key not set.")

# ---------------------- Save Results ----------------------
def save_to_file(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Data Science Jokes from Various Models\n\n")
        f.writelines(outputs)
    print(f"\n✅ All model responses saved to: {path}")

# ---------------------- DeepSeek Advanced Section ----------------------
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

# ---------------------- GPT-4o & Claude Conversation Demo ----------------------
def run_conversation_demo(openai_client, claude_client):
    print("\n🎭 GPT-4o-mini vs Claude-3-Haiku Conversation")

    gpt_model = "gpt-4o-mini"
    claude_model = "claude-3-haiku-20240307"

    gpt_system = "You are a chatbot who is very argumentative; you challenge everything in a snarky way."
    claude_system = "You are a very polite chatbot who tries to agree and calm things down."

    gpt_messages = ["Hi there"]
    claude_messages = ["Hi"]

    def call_gpt():
        messages = [{"role": "system", "content": gpt_system}]
        for gpt, claude in zip(gpt_messages, claude_messages):
            messages.append({"role": "assistant", "content": gpt})
            messages.append({"role": "user", "content": claude})
        completion = openai_client.chat.completions.create(model=gpt_model, messages=messages)
        return completion.choices[0].message.content

    def call_claude():
        messages = []
        for gpt, claude_msg in zip(gpt_messages, claude_messages):
            messages.append({"role": "user", "content": gpt})
            messages.append({"role": "assistant", "content": claude_msg})
        messages.append({"role": "user", "content": gpt_messages[-1]})
        reply = claude_client.messages.create(
            model=claude_model,
            system=claude_system,
            messages=messages,
            max_tokens=500
        )
        return reply.content[0].text

    print(f"GPT:\n{gpt_messages[0]}\n")
    print(f"Claude:\n{claude_messages[0]}\n")

    for _ in range(5):
        gpt_reply = call_gpt()
        print(f"GPT:\n{gpt_reply}\n")
        gpt_messages.append(gpt_reply)

        claude_reply = call_claude()
        print(f"Claude:\n{claude_reply}\n")
        claude_messages.append(claude_reply)

# ---------------------- Main ----------------------
if __name__ == "__main__":
    keys = setup_environment()
    check_api_keys(keys)
    generate_model_jokes(keys)
    save_to_file(keys["output_path"])
    deepseek_advanced(keys)

    # GPT-4o vs Claude Haiku conversation
    openai_client = OpenAI()
    claude_client = anthropic.Anthropic()
    run_conversation_demo(openai_client, claude_client)
