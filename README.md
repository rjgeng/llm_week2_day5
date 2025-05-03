# OpenAI API Billing Incident

### 🙏 With thanks to Ed Donner
This repo is part of my learning journey through the Udemy course *LLM Engineering: Master AI, Large Language Models & Agents* by [Ed Donner](https://www.linkedin.com/in/eddonner/). His guidance helped me turn a mistake into a lesson — and a case study.

I'm currently learning from the Udemy course [**LLM Engineering: Master AI, Large Language Models & Agents**](https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models), taught by [Ed Donner](https://www.linkedin.com/in/eddonner/).

On **April 23, 2025**, while working on code from **Week 2, Day 5**, I accidentally triggered a billing incident that cost me **$132.42 within 30 minutes**.

> 🔗 **GitHub Repository:**  
> [github.com/rjgeng/openai_api_billing_incident](https://github.com/rjgeng/openai_api_billing_incident)

---

## 🔥 What Happened

While rewriting the original `day5.ipynb` into a Python script (`day5.py`) and enhancing it into a Gradio app (`airline_multi-modal.py`, now evolved into `flightai_tts_safe_multi_modal.py`), I encountered two critical issues:

- ❌ **No usage limit set** → the default Tier 1 plan allowed billing up to $120 without real-time alerts.
- ❌ **TTS loop bug** → my code called `talker()` with a large `chatlog.md`, triggering massive character-based charges.

The result:
- ~**25 DALL·E 3 image generations** (~$40)
- ~**8.8 million characters** sent to **Text-to-Speech (TTS)** (~$80+)
- Several `429 Too Many Requests` errors occurred, but billing continued silently in the background.

---

## 📸 Screenshots

### 🧾 Billing Summary  
![Billing Screenshot](./week2/scripts/day5/billing_incident/incident_activity_&_cost/billing_page_screenshot.png)

### 📊 Usage Overview  
![Usage Screenshot](./week2/scripts/day5/billing_incident/incident_activity_&_cost/usage_page_screenshot.png)

### ⚙️ API Limit Page  
![Limit Screenshot](./week2/scripts/day5/billing_incident/incident_activity_&_cost/limit_page_screenshot.png)

---

## 🕒 Postmortem Timeline 

| Time       | Event Description                                                                                     |
|------------|------------------------------------------------------------------------------------------------------|
| 09:06 AM   | Started running `airline_multi-modal.py` with TTS + DALL·E                                           |
| 09:06 AM   | `chatlog.md` generated, triggered TTS, then app crashed (Error 429), assumed no cost incurred        |
| 09:30 AM   | Realized billing hit negative **-$87.66** after refreshing the billing page                          |
| 09:49 AM   | Added $90 manually → Balance shown as **+$12.34**                                                    |
| 10:15 AM   | Re-ran app with same bug, `chatlog.md` regenerated, TTS re-triggered                                 |
| 10:15 AM   | Account dropped to **–$33.96**, total cost **$132.42**                                               |
| May 1st    | Account balance reset to **$0.00**; unpaid balance later charged to credit card on May 2nd           |
| May 2nd    | Received invoice **6B50A431-0003**, confirming **$33.95 charged to credit card**                     |

📎 [View Invoice PDF](./week2/scripts/day5/billing_incident/incident_activity_&_cost/Receipt-2279-2005.pdf)

---

## 🧠 Lessons Learned

- ✅ Set **monthly usage caps** before running anything on a real API key.
- ✅ Understand TTS pricing: it charges per **character**, not per request.
- ✅ Always include **error handling** and retry logic with rate limits.
- ✅ Be careful logging full conversation history into files TTS reads from.
- ✅ Use **API-based usage monitoring** for more reliable alerts than the dashboard.

---

## 🧩 Code Snippet – TTS Triggered Loop

```python
if enable_tts:
    try:
        talker(reply)
    except RateLimitError:
        history.append({"role": "assistant", "content": "⚠️ TTS quota exceeded."})
