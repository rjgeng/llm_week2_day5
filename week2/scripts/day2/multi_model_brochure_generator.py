import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai
import cohere  # ✅ Add Cohere support

# ------------------ Setup ------------------ #
def setup_environment():
    load_dotenv(override=True)
    return {
        "openai_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        "google_key": os.getenv("GOOGLE_API_KEY"),
        "deepseek_key": os.getenv("DEEPSEEK_API_KEY"),
        "cohere_key": os.getenv("COHERE_API_KEY")  # ✅ Cohere key
    }

key_list = setup_environment()

# ------------------ Website Scraper ------------------ #
class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title"
            body = soup.body
            if body:
                for tag in body(["script", "style", "img", "input"]):
                    tag.decompose()
                self.text = body.get_text(separator="\n", strip=True)
            else:
                self.text = soup.get_text(separator="\n", strip=True)[:3000] or "No readable content."
        except Exception as e:
            self.title = "Fetch Error"
            self.text = f"Could not fetch webpage: {e}"

    def get_contents(self):
        return f"Webpage Title: {self.title}\n\nLanding Page Content:\n{self.text}"

# ------------------ Model Prompt ------------------ #
system_message = (
    "You are an assistant that analyzes the contents of a company website landing page "
    "and creates a short brochure about the company for prospective customers, investors, and recruits. "
    "Respond in markdown."
)

# ------------------ Model Streamers ------------------ #
def stream_gpt(prompt):
    client = OpenAI(api_key=key_list["openai_key"])
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    try:
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        result = ""
        for chunk in stream:
            piece = chunk.choices[0].delta.content or ""
            print("🧩 GPT Chunk:", piece)
            result += piece
            yield result
    except Exception as e:
        yield f"❌ GPT error: {e}"

def stream_claude(prompt):
    client = anthropic.Anthropic(api_key=key_list["anthropic_key"])
    try:
        result = client.messages.stream(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7,
            system=system_message,
            messages=[{"role": "user", "content": prompt}],
        )
        response = ""
        with result as stream:
            for text in stream.text_stream:
                print("🧩 Claude Chunk:", text)
                response += text or ""
                yield response
    except Exception as e:
        yield f"❌ Claude error: {e}"

def stream_gemini(prompt):
    try:
        genai.configure(api_key=key_list["google_key"])
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_message
        )
        chat = model.start_chat()
        response = chat.send_message(prompt)
        yield response.text
    except Exception as e:
        yield f"❌ Gemini error: {e}"

def stream_deepseek(prompt):
    try:
        client = OpenAI(api_key=key_list["deepseek_key"], base_url="https://api.deepseek.com")
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True
        )
        result = ""
        for chunk in response:
            piece = chunk.choices[0].delta.content or ""
            print("🧩 DeepSeek Chunk:", piece)
            result += piece
            yield result
    except Exception as e:
        yield f"❌ DeepSeek error: {e}"

def stream_cohere(prompt):  # ✅ New Cohere streamer
    try:
        client = cohere.Client(api_key=key_list["cohere_key"])
        reply = ""
        response = client.chat_stream(
            message=prompt,
            model="command-r-plus",
            temperature=0.7,
            preamble=system_message
        )
        for event in response:
            if event.event_type == "text-generation":
                print("🧩 Cohere Chunk:", event.text)
                reply += event.text
                yield reply
    except Exception as e:
        yield f"❌ Cohere error: {e}"

# ------------------ Brochure Generator ------------------ #
def stream_brochure(company_name, url, model):
    website = Website(url)
    prompt = f"Please generate a company brochure for {company_name} based on the following landing page:\n\n"
    prompt += website.get_contents()

    print("\n📥 Prompt sent to model:\n", prompt[:1000])
    yield "🌀 Generating brochure..."

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/{company_name.replace(' ', '_')}_{model}_{timestamp}.md"

    content = ""
    if model == "GPT":
        for chunk in stream_gpt(prompt):
            content = chunk
            yield chunk
    elif model == "Claude":
        for chunk in stream_claude(prompt):
            content = chunk
            yield chunk
    elif model == "Gemini":
        for chunk in stream_gemini(prompt):
            content = chunk
            yield chunk
    elif model == "DeepSeek":
        for chunk in stream_deepseek(prompt):
            content = chunk
            yield chunk
    elif model == "Cohere":  # ✅ Add Cohere
        for chunk in stream_cohere(prompt):
            content = chunk
            yield chunk
    else:
        yield "❌ Invalid model selected."
        return

    try:
        os.makedirs("output", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving markdown: {e}")

# ------------------ Launch Gradio ------------------ #
demo = gr.Interface(
    fn=stream_brochure,
    inputs=[
        gr.Textbox(label="Company Name"),
        gr.Textbox(label="Website URL (include https://)", value="https://huggingface.co"),
        gr.Dropdown(["GPT", "Claude", "Gemini", "DeepSeek", "Cohere"], label="Select Model", value="GPT")  # ✅ Add Cohere
    ],
    outputs=gr.Markdown(label="Generated Brochure"),
    title="📄 Company Brochure Generator (GPT + Claude + Gemini + DeepSeek + Cohere)",
    description="Scrape a landing page and generate a markdown brochure using your preferred LLM",
    allow_flagging="never"
)

if __name__ == "__main__":
    demo.launch()
