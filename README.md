# Folio — AI Resume Portfolio Generator

> Convert your resume into a professional portfolio webpage using the Google Gemini API.

Built with **Python · Flask · Google Gemini API · Jinja2 · HTML · CSS · JavaScript**

---

## Features

- **Two ways to generate:** CLI (`python main.py`) or interactive Web App (`python backend/app.py`)
- **AI-powered extraction:** Gemini parses your resume into structured JSON — name, headline, summary, skills, education, experience, projects, achievements, and contact info
- **4 portfolio templates:** Clean, Developer (dark mode), Creative, and Minimal
- **Human review step:** Every extracted field is shown to you before the portfolio is rendered — nothing goes into your portfolio without your approval
- **Empty section hiding:** Sections with no data are automatically omitted
- **Self-contained HTML output:** The generated `portfolio.html` works offline with no external dependencies
- **Desktop + mobile preview:** Toggle between viewport sizes before downloading
- **Responsible by design:** The prompt strictly forbids Gemini from inventing any information

---

## Project Structure

```
AI-resume-portfolio-generator/
│
├── main.py                  # CLI entry point: resume.txt → portfolio.html
├── resume.txt               # Sample resume (fictional — replace with your own)
├── portfolio.html           # Sample generated output
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
│   │   ├── template_1.html  # Clean template
│   │   ├── template_2.html  # Developer (dark) template
│   │   ├── template_3.html  # Creative template
│   │   ├── template_4.html  # Minimal template
│   │   └── portfolio.html   # Legacy portfolio template
│   └── static/
│       ├── template1.css    # Styles for template 1
│       ├── template2.css    # Styles for template 2
│       ├── template3.css    # Styles for template 3
│       ├── template4.css    # Styles for template 4
│       └── style.css        # Legacy styles
│
├── screenshots/             # Application screenshots (see screenshots/README.md)
├── requirements.txt         # Python dependencies (pinned versions)
├── .env.example             # Environment variable template
├── .gitignore               # Git exclusions
└── AI_USAGE_LOG.md          # Record of AI tools used during development
```

---

## Requirements

- Python 3.10 or higher
- A Google Gemini API key ([get one free at Google AI Studio](https://aistudio.google.com/))

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-username/AI-resume-portfolio-generator.git
cd AI-resume-portfolio-generator
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure your API key**
```bash
# Copy the example file
cp .env.example .env

# Open .env and add your key
GEMINI_API_KEY=your_actual_key_here
```

> **Never commit your real `.env` file.** It is listed in `.gitignore`.

---

## Running the Project

### Option 1 — CLI (matches the brief's primary workflow)

```bash
python main.py
```

This reads `resume.txt`, sends it to Gemini, and writes `portfolio.html` to the project root.

```bash
# Optional arguments:
python main.py --resume my_cv.txt         # use a custom resume file
python main.py --template 2               # use Developer (dark) template
python main.py --output my_portfolio.html # custom output filename

# All templates:
# 1 = Clean (default)   2 = Developer   3 = Creative   4 = Minimal
```

### Option 2 — Web App (full interactive experience)

```bash
python backend/app.py
```

Open `http://127.0.0.1:5000` in your browser. The web app walks you through:
1. Paste your resume or upload a `.txt` file
2. Review every AI-extracted field before rendering
3. Choose a template
4. Preview the portfolio (desktop + mobile)
5. Download as a standalone `portfolio.html`

---

## Running Tests

```bash
python backend/test_app.py
```

All 6 test cases from the brief are covered:

| Test | Description |
|---|---|
| Test 1 | No file uploaded → HTTP 400 with clear error |
| Test 2 | Resume too short → HTTP 400 with clear error |
| Test 3 | Missing API key → `RuntimeError` at startup |
| Test 4 | Valid resume → HTTP 200 with rendered HTML |
| Test 5 | Invalid API key → HTTP 502 with error message |
| Test 6 | Invalid JSON from Gemini → HTTP 500 with error message |

---

## How It Works

```
resume.txt
    │
    ▼
[Python] Read + clean text (strip blanks, collapse whitespace)
    │
    ▼
[Gemini API] Strict prompt → returns structured JSON only
    │
    ▼
[Python] Parse JSON → fill defaults for missing fields
    │
    ▼
[Jinja2] Render HTML template with the parsed data
    │
    ▼
portfolio.html  (self-contained, works offline)
```

---

## Prompt Design

The Gemini prompt is defined in `backend/portfolio_builder.py`. It enforces 7 strict rules:

1. Return **only** the JSON object — no markdown fences, no explanation
2. Use **only** information explicitly stated in the resume — never invent anything
3. Missing fields → empty string `""` or empty array `[]` — never guess
4. Summary must be **2–3 sentences maximum**, strictly factual
5. Skills must be a **flat array** taken directly from the resume
6. Achievements must be **explicitly stated** in the resume — no inferences
7. Contact sub-fields are only populated if **explicitly present** in the resume

### Known Limitations and Hallucination Risks

- Gemini may **misread formatting** in complex resumes (e.g., confusing a project description with job experience)
- Gemini may **merge or split** similar sections if the resume structure is ambiguous
- Dates, company names, and technologies are high-risk fields — always verify these
- The summary, even with constraints, may occasionally paraphrase in ways that subtly overstate a claim
- **The Review step is your responsibility.** Every generated claim must be checked against your original resume before submission or sharing.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.13 | Core application logic |
| Flask 3.1.3 | Web server and routing |
| Google Gemini API (`google-genai`) | AI resume parsing |
| Jinja2 | HTML template rendering |
| `python-dotenv` | Environment variable management |
| HTML + CSS + JavaScript | Frontend UI and portfolio templates |

---

## Optional Enhancements Implemented

Beyond the brief's minimum requirements, this project includes:

- ✅ **4 portfolio templates** (brief requires at least 1)
- ✅ **Interactive web app** with a 7-screen step-by-step flow
- ✅ **Human review step** — every AI field is editable before rendering
- ✅ **Desktop/mobile preview toggle** in the preview screen
- ✅ **Exponential backoff retries** on Gemini 429/503 errors
- ✅ **Inline CSS** in generated HTML — fully offline, no CDN dependencies
- ✅ **CLI entry point** (`main.py`) — runs without a browser

---

## AI Usage

This project was built with AI assistance. See [`AI_USAGE_LOG.md`](./AI_USAGE_LOG.md) for a full record of what was AI-generated, what prompts were used, and what the team changed before using the output.

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
