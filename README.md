# OpenAI API Billing Incident

I'm currently learning from the Udemy course [**LLM Engineering: Master AI, Large Language Models & Agents**](https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models), taught by [Ed Donner](https://www.linkedin.com/in/eddonner/).

On **April 23, 2025**, while working on the code from **Week 2, Day 5**, I accidentally triggered a billing incident that cost me **$132.42 within 30 minutes**.

---

## 🔥 What Happened

While converting the `day5.ipynb` Jupyter notebook into a Python script (`day5.py`) and extending it with my own Gradio app (`airline_multi-modal.py`), I ran into two key mistakes:

- **No usage limit was set** — the default billing tier (Usage Tier 1) allowed spending up to $120 before any alert, causing my account to go into the negative after my $10 initial credit was exhausted.
- **A logic bug in my code caused repeated TTS (Text-to-Speech) requests** — attempting to read large Markdown files like `chatlog.md` multiple times, silently accumulating charges.

The result:
- ~**25 image generations** with DALL·E 3 (~$40)
- ~**8.8 million characters** sent to the TTS engine (~$80–90)
- Several `429` errors appeared while I kept refreshing the billing dashboard, unaware of the pending costs.

---

## 🧠 Lessons Learned

- Monitor **usage and billing dashboards** frequently — they're **not real-time** and can lag during rapid requests.
- Set **usage caps** and implement **API key rotation** and **2FA**.
- Always double-check code for infinite loops or silent retries, especially when using cost-bearing features like TTS or image generation.
- Don’t rely only on UI feedback — even an error can still incur charges.

---

## 💻 Project Structure

```plaintext
/llm_engineering
├── week1/...
├── week2
│  ├── scripts
│  │    ├── day5
│  │    │    ├── billing_incident
│  │    │    │    ├── incident_activity_&_cost
│  │    │    │    │    ├── activity-2025-04-23-2025-04-24.csv
│  │    │    │    │    ├── cost_2025-03-24_2025-04-23.csv
│  │    │    │    │    ├── billing_page_screenshot.png
│  │    │    │    │    ├── usage_page_screenshot.png
│  │    │    │    │    ├── limit_page_screenshot.png
│  │    │    │    │    └── incident_analysis_by_chatgpt.md
│  │    │    │    └── incident_running-time_files_generated/
│  │    │    │         ├── chatlog.md
│  │    │    │         ├── london_*.png
│  │    │    │         └── session_*.md
│  │    │    ├── day5.py                       ← Converted Jupyter notebook demo
│  │    │    ├── airline_multi-modal.py        ← Extended version with Gradio
│  │    │    └── chatlog.md                    ← Output file that triggered TTS
│  └── Jupyter Notebook/
│        └── day5.ipynb                        ← Original Udemy lesson
└── .env                                       ← API key (not committed)
