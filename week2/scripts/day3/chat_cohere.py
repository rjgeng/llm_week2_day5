# cohere_chat_demo.py
import os
import cohere
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Initialize Cohere client
co = cohere.Client(COHERE_API_KEY)

def chat_with_cohere():
    chat_history = []
    print("👋 Start chatting with Cohere! Type 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("🛑 Ending chat.")
            break

        try:
            response = co.chat(
                message=user_input,
                chat_history=chat_history,
                model="command-r-plus",  # You can try "command-r" or others if this doesn't work
            )
            reply = response.text
            print(f"Cohere: {reply}")
            chat_history.append({"role": "USER", "message": user_input})
            chat_history.append({"role": "CHATBOT", "message": reply})
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    chat_with_cohere()

