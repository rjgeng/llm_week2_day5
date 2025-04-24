import streamlit as st
from multi_model_joke import generate_all_jokes
from datetime import datetime
import os

st.set_page_config(page_title="😂 Multi-Model Joke Generator", layout="wide")

st.title("😂 Multi-Model Joke Generator for Data Scientists")

st.markdown("""
Welcome to the ultimate LLM showdown! Click the **Generate Jokes** button to see what each model brings to the (comedy) table. All jokes are light-hearted and meant for a Data Science audience.
""")

# Generate jokes when button clicked
if st.button("Generate Jokes"):
    with st.spinner("Fetching jokes from all models..."):
        results = generate_all_jokes()
    
    st.success("All jokes generated successfully!")

    st.markdown("## 🤖 Model Responses")
    for model_name, content in results.items():
        st.markdown(f"### {model_name}")
        st.markdown(content)

    # Ensure output directory exists
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../output"))
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(output_dir, f"jokes_{timestamp}.md")

    # Save all results to markdown
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Data Science Jokes from Various Models\n\n")
        for model, text in results.items():
            f.write(f"## {model}\n\n{text.strip()}\n\n")

    st.markdown(f"✅ Saved output to `{output_path}`")

else:
    st.info("Click the button to get jokes from OpenAI, Claude, and Gemini.")
