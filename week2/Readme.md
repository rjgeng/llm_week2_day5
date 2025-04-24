# week 2 Projects

## 🧩 Project Structure

```vbet
/llm_engineering
├── week2 
│  ├── multi_model_joke_demo                                    ← Streamlit App
│  │    ├── app.py                                              ← Streamlit UI
│  │    └── multi_model_joke.py                                 ← Logic (scraping, OpenAI call)
│  ├── scripts 
│  │    ├── ai_conversations                                            
│  │    │     ├── message_chat_gpt_vs_claude.py                 ← Gradio UI App   
│  │    │     ├── streaming_chat_gpt_vs_claude.py               ← Gradio UI App   
│  │    │     ├── message_chat_deepseek_vs_gpt.py               ← Gradio UI App   
│  │    │     ├── streaming_chat_deepseek_vs_gpt.py             ← Gradio UI App   
│  │    │     ├── message_chat_deepseek_vs_claude.py            ← Gradio UI App   
│  │    │     └── message_chat_deepseek_vs_gemini.py            ← Gradio UI App   
│  │    ├── day1                                             
│  │    │     ├── day1.py                                       ← Standalone python script         
│  │    │     ├── ai_conversations.py                           ← Standalone python script         
│  │    │     └── deepseek_model.py                             ← Standalone python script         
│  │    ├── day2                                             
│  │    │     ├── day2.py                                       ← Gradio UI App    
│  │    │     ├── Message_vs_Stream.py                          ← Gradio UI App   
│  │    │     ├── multi_model_brochure_generator.py             ← Gradio UI App   
│  │    │     ├── message_multi_model_chat.py                   ← Gradio UI App   
│  │    │     ├── streaming_multi_model_chat.py                 ← Gradio UI App   
│  │    │     ├── message_multi_model_news_chat.py              ← Gradio UI App   
│  │    │     └── streaming_multi_model_news_chat.py            ← Gradio UI App
│  │    ├── day3                                             
│  │    │     ├── day3.py                                       ← Gradio UI App    
│  │    │     ├── chat_llama_demo.py                            ← Gradio UI App    
│  │    │     ├── chat_cohere_demo.py                            ← Gradio UI App    
│  │    │     └── chat_demo.py                                  ← Gradio UI App    
│  │    ├── day4                                            
│  │    │     ├── day4.py                                       ← Gradio UI App    
│  │    │     ├── airline_ai_ollama.py                                       ← Gradio UI App    
│  │    │     └── airline_multi_modle.py                       ← Gradio UI App    
│  │    └── day5
│  │    │     ├── day4.py                                       ← Gradio UI App    
│  │    │     └── xxx_demo.py                                   ← Gradio UI App   
│  └── output/                                                  ← Saved markdown brochures
└── .env                                                        ← API key
```

## 🚀 Run Gradio APP Locally:

```bash
python gradio_chat_app.py
```

## ▶️ RunStreamlit App Locally

```bash
streamlit run app.py
```

### Note: AI Chatbot Terminology: Developer vs UI Language

| Dev Term         | UI Label (Alias)     | Description |
|------------------|----------------------|-------------|
| `prompt`         | Your Message         | The user's input or question |
| `system_message` | AI Personality / Behavior | Instruction that defines assistant's tone (e.g., polite, sarcastic) |
| `user`           | You                  | Role of the human in the conversation |
| `assistant`      | AI                   | Role of the model in the conversation |
| `message`        | Full Response        | The complete response generated at once |
| `stream`         | Live Response        | The AI responds word-by-word or token-by-token |
| `completion`     | AI Reply             | The model's actual response to input |
| `delta` (streaming) | (Hidden in UI)    | The small chunk of response streamed in real-time |
| `chat_history`   | Conversation Log     | The full history of back-and-forth turns |
| `model`          | Model Name           | The underlying LLM used (e.g., GPT-4o, Claude 3) |
| `temperature`    | Creativity Level     | Controls randomness; higher = more creative |
| `max_tokens`     | Response Length Limit | Maximum number of tokens in the response |
| `role`           | (Hidden)             | Internal indicator: "system", "user", "assistant" |



