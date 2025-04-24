import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import google.generativeai

load_dotenv(override=True)

openai = OpenAI()
claude = anthropic.Anthropic()
google.generativeai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

system_message = "You are an assistant that is great at telling jokes"
user_prompt = "Tell a light-hearted joke for an audience of Data Scientists"

prompts = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": user_prompt}
]

def generate_all_jokes():
    results = {}

    # OpenAI
    try:
        response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=prompts)
        results["GPT-3.5-Turbo"] = response.choices[0].message.content
    except Exception as e:
        results["GPT-3.5-Turbo"] = f"❌ Error: {str(e)}"

    try:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=prompts, temperature=0.7)
        results["GPT-4o-Mini"] = response.choices[0].message.content
    except Exception as e:
        results["GPT-4o-Mini"] = f"❌ Error: {str(e)}"

    try:
        response = openai.chat.completions.create(model="gpt-4o", messages=prompts, temperature=0.4)
        results["GPT-4o"] = response.choices[0].message.content
    except Exception as e:
        results["GPT-4o"] = f"❌ Error: {str(e)}"

    # Claude
    try:
        response = claude.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=200,
            temperature=0.7,
            system=system_message,
            messages=[{"role": "user", "content": user_prompt}]
        )
        results["Claude 3.5 Sonnet"] = response.content[0].text
    except Exception as e:
        results["Claude 3.5 Sonnet"] = f"❌ Error: {str(e)}"

    # Gemini
    try:
        gemini = google.generativeai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=system_message
        )
        response = gemini.generate_content(user_prompt)
        results["Gemini 2.0 (via SDK)"] = response.text
    except Exception as e:
        results["Gemini 2.0 (via SDK)"] = f"❌ Error: {str(e)}"

    # Gemini via OpenAI-compatible API
    try:
        gemini_openai = OpenAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        response = gemini_openai.chat.completions.create(model="gemini-2.0-flash-exp", messages=prompts)
        results["Gemini 2.0 (OpenAI-Compatible API)"] = response.choices[0].message.content
    except Exception as e:
        results["Gemini 2.0 (OpenAI-Compatible API)"] = f"❌ Error: {str(e)}"

    return results
