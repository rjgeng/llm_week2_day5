import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
import anthropic

# ------------------ Load Keys ------------------ #
load_dotenv()
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

system_message = (
    "You are an assistant that analyzes the contents of a company website landing page "
    "and creates a short brochure about the company for prospective customers, investors, and recruits. "
    "Respond in markdown."
)

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


# ------------------ GPT Stream ------------------ #
def stream_gpt(prompt):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    try:
        stream = openai.chat.completions.create(
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


# ------------------ Claude Stream ------------------ #
def stream_claude(prompt):
    try:
        result = claude.messages.stream(
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


# ------------------ Brochure Generator ------------------ #
def stream_brochure(company_name, url, model):
    website = Website(url)
    prompt = f"Please generate a company brochure for {company_name} based on the following landing page:\n\n"
    prompt += website.get_contents()

    print("\n📥 Prompt sent to model:\n", prompt[:1000])
    yield "🌀 Generating brochure..."

    if model == "GPT":
        yield from stream_gpt(prompt)
    elif model == "Claude":
        yield from stream_claude(prompt)
    else:
        yield "❌ Invalid model selected."


# ------------------ Optional Debug Test Interface ------------------ #
def test_gpt():
    yield from stream_gpt("Tell me a joke about AI.")

# ------------------ Launch Gradio ------------------ #
demo = gr.Interface(
    fn=stream_brochure,
    inputs=[
        gr.Textbox(label="Company Name"),
        gr.Textbox(label="Website URL (include https://)", value="https://huggingface.co"),
        gr.Dropdown(["GPT", "Claude"], label="Select Model", value="GPT")
    ],
    outputs=gr.Markdown(label="Generated Brochure"),
    title="📄 Company Brochure Generator (GPT + Claude)",
    description="Scrape a landing page and generate a markdown brochure using GPT or Claude",
    allow_flagging="never"
)

# Uncomment below to run test UI:
# test_ui = gr.Interface(fn=test_gpt, inputs=[], outputs=gr.Markdown())
# test_ui.launch()

# Launch the main app
demo.launch()
