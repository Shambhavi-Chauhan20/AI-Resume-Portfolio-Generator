<div align="center">

# ✨ Folio — AI Resume Portfolio Generator

### *Turn your resume into a stunning portfolio webpage in seconds — powered by Google Gemini AI* 🚀

[![Live Demo](https://img.shields.io/badge/🌐%20Live%20Demo-Visit%20Now-6c47ff?style=for-the-badge)](https://ai-resume-portfolio-generator-r9lp.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-API-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

</div>

---

## 🎯 What is Folio?

**Folio** takes your plain-text resume, sends it to Google's Gemini AI, and instantly generates a beautiful, professional portfolio webpage — no design skills needed.

> 🔗 **Try it live:** [ai-resume-portfolio-generator-r9lp.onrender.com](https://ai-resume-portfolio-generator-r9lp.onrender.com)

---

## ⚡ Features

| Feature | Details |
|---|---|
| 🤖 **AI-Powered Extraction** | Gemini parses name, headline, summary, skills, education, experience, projects, achievements & contact |
| 🎨 **4 Portfolio Templates** | Clean · Developer (dark mode) · Creative · Minimal |
| 👀 **Human Review Step** | Every AI-extracted field is shown to you before rendering — nothing goes to your portfolio without approval |
| 🙈 **Smart Section Hiding** | Sections with no data are automatically omitted |
| 📦 **Self-Contained Output** | Generated `portfolio.html` works fully offline — no CDN dependencies |
| 📱 **Desktop + Mobile Preview** | Toggle between viewport sizes before downloading |
| 🔒 **Responsible AI** | The prompt strictly forbids Gemini from inventing any information |
| 🔁 **Auto Retry** | Exponential backoff on Gemini 429/503 errors |
| 💻 **CLI + Web App** | Use it headlessly or through a beautiful step-by-step web interface |

---

## 🗂️ Project Structure

```
AI-resume-portfolio-generator/
│
├── 🐍 main.py                  # CLI entry point: resume.txt → portfolio.html
├── 📄 resume.txt               # Sample resume (replace with your own)
│
├── backend/
│   ├── app.py               # Flask routes and upload handling
│   ├── gemini_client.py     # Gemini API setup and request logic
│   ├── portfolio_builder.py # Prompt design, JSON parsing, HTML rendering
│   └── test_app.py          # Unit tests (6 test cases)
│
├── frontend/
│   ├── templates/
│   │   ├── index.html       # Main SPA (all 7 screens)
│   │   ├── template_1.html  # 🪄 Clean template
│   │   ├── template_2.html  # 🌑 Developer (dark) template
│   │   ├── template_3.html  # 🎨 Creative template
│   │   └── template_4.html  # 🧘 Minimal template
│   └── static/
│       ├── template1.css – template4.css
│       └── style.css
│
├── 📸 screenshots/
├── 📋 requirements.txt
├── 🔐 .env.example
└── 📝 AI_USAGE_LOG.md
```

---

## 🛠️ Setup & Installation

### Prerequisites
- 🐍 Python **3.10+**
- 🔑 A Google Gemini API key — [get one free at Google AI Studio](https://aistudio.google.com/)

### Step-by-step

**1️⃣ Clone the repo**
```bash
git clone https://github.com/Shambhavi-Chauhan20/AI-Resume-Portfolio-Generator.git
cd AI-Resume-Portfolio-Generator
```

**2️⃣ Install dependencies**
```bash
pip install -r requirements.txt
```

**3️⃣ Add your API key**
```bash
cp .env.example .env
# Open .env and set:
GEMINI_API_KEY=your_actual_key_here
```

> ⚠️ **Never commit your real `.env` file** — it's already in `.gitignore`.

---

## 🚀 Running the Project

### 🌐 Option 1 — Web App *(recommended)*

```bash
python backend/app.py
```

Open `http://127.0.0.1:5000` and follow the 4-step flow:

```
📄 Upload Resume  →  👀 Review Fields  →  🎨 Pick Template  →  📥 Download Portfolio
```

### 🖥️ Option 2 — CLI

```bash
python main.py

# With options:
python main.py --resume my_cv.txt --template 2 --output my_portfolio.html

# Templates:  1 = Clean  |  2 = Developer  |  3 = Creative  |  4 = Minimal
```

---

## 🧪 Running Tests

```bash
python backend/test_app.py
```

| # | Test | Expected |
|---|---|---|
| 1 | No file uploaded | HTTP 400 with clear error |
| 2 | Resume too short | HTTP 400 with clear error |
| 3 | Missing API key | `RuntimeError` at startup |
| 4 | Valid resume | HTTP 200 with rendered HTML |
| 5 | Invalid API key | HTTP 502 with error message |
| 6 | Invalid JSON from Gemini | HTTP 500 with error message |

---

## 🔄 How It Works

```
📄 resume.txt
      │
      ▼
🐍 Python — Read + clean text (strip blanks, collapse whitespace)
      │
      ▼
🤖 Gemini API — Strict prompt → returns structured JSON only
      │
      ▼
🐍 Python — Parse JSON → fill defaults for missing fields
      │
      ▼
🖼️ Jinja2 — Render HTML template with the parsed data
      │
      ▼
✅ portfolio.html (self-contained, works fully offline)
```

---

## 🧠 Prompt Design

The Gemini prompt lives in [`backend/portfolio_builder.py`](./backend/portfolio_builder.py) and enforces **7 strict rules**:

1. 🚫 Return **only** the JSON object — no markdown fences, no explanation
2. 🚫 Use **only** information explicitly stated in the resume — never invent anything
3. 🚫 Missing fields → `""` or `[]` — never guess
4. ✂️ Summary must be **2–3 sentences max**, strictly factual
5. 🗂️ Skills must be a **flat array** taken directly from the resume
6. 🏆 Achievements must be **explicitly stated** — no inferences
7. 📬 Contact fields only populated if **explicitly present** in the resume

### ⚠️ Known Limitations

- Gemini may misread formatting in complex or multi-column resumes
- Dates, company names, and technologies are high-risk — always verify
- **The Review step is your responsibility** — check every field before sharing

---

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python 3.13 | Core application logic |
| 🌶️ Flask 3.1 | Web server and routing |
| 🤖 Google Gemini API | AI resume parsing |
| 🖼️ Jinja2 | HTML template rendering |
| 🔐 `python-dotenv` | Environment variable management |
| 🎨 HTML + CSS + JS | Frontend UI and portfolio templates |

---

## 🌟 Extras Beyond the Brief

- ✅ **4 portfolio templates** (brief required at least 1)
- ✅ **Interactive web app** with a 7-screen step-by-step flow
- ✅ **Human review step** — every AI field is editable before rendering
- ✅ **Desktop/mobile preview toggle**
- ✅ **Exponential backoff retries** on Gemini 429/503 errors
- ✅ **Inline CSS** — generated HTML is fully offline, no CDN needed
- ✅ **CLI entry point** — runs without a browser
- ✅ **Deployed on Render** — live at [ai-resume-portfolio-generator-r9lp.onrender.com](https://ai-resume-portfolio-generator-r9lp.onrender.com)

---

## 🤖 AI Usage

This project was built with AI assistance. See [`AI_USAGE_LOG.md`](./AI_USAGE_LOG.md) for a full record of what was AI-generated, what prompts were used, and what was changed before use.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">

Made with ❤️ by [Shambhavi Chauhan](https://github.com/Shambhavi-Chauhan20)

⭐ *If you found this useful, give it a star!* ⭐

</div>
