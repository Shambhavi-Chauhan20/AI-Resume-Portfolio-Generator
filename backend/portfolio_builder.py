"""
portfolio_builder.py
Owns: prompt design, Gemini response parsing, and HTML portfolio rendering.

Public interface consumed by app.py:
    build_prompt(cleaned_text: str) -> str
    build_portfolio(gemini_raw_response: str) -> str
"""

import json
import re

from flask import render_template


# ---------------------------------------------------------------------------
# URL sanitization — only allow http/https to prevent javascript: XSS
# ---------------------------------------------------------------------------
def _safe_url(url: str) -> str:
    """Return the URL only if it starts with http:// or https://. Empty string otherwise."""
    if url and isinstance(url, str):
        stripped = url.strip()
        if stripped.lower().startswith(("https://", "http://")):
            return stripped
    return ""


# ---------------------------------------------------------------------------
# Schema defaults — every key the template expects must be present.
# ---------------------------------------------------------------------------
_SCHEMA_DEFAULTS: dict = {
    "name": "",
    "headline": "",
    "summary": "",
    "skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "achievements": [],
    "contact": {
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
    },
}

_EDUCATION_DEFAULTS = {"degree": "", "institution": "", "year": ""}
_EXPERIENCE_DEFAULTS = {"title": "", "company": "", "dates": "", "description": ""}
_PROJECT_DEFAULTS = {"title": "", "description": "", "technologies": []}


# ---------------------------------------------------------------------------
# Task 1 — Prompt design
# ---------------------------------------------------------------------------
def build_prompt(cleaned_text: str) -> str:
    """
    Returns the full prompt string to send to Gemini.

    Rules enforced in the prompt:
    - Use ONLY information present in the resume — never invent anything.
    - Return JSON only (no markdown fences, no preamble, no trailing text).
    - Missing fields → empty string or empty list, never guessed values.
    - Summary must be concise (2-3 sentences max) and strictly factual.
    """
    return f"""You are a JSON-only data extractor. Your task is to parse the resume text below and return a single, valid JSON object.

STRICT RULES — violating any of these will cause the output to be rejected:
1. Return ONLY the JSON object. Do NOT include markdown code fences (```), the word "json", any explanation, preamble, or trailing text of any kind.
2. Use ONLY information that is explicitly stated in the resume. Do NOT invent, infer, assume, or hallucinate ANY skills, job titles, company names, dates, project names, technologies, achievements, URLs, emails, phone numbers, or any other data.
3. If a field's information is not present in the resume, use an empty string "" for string fields or an empty array [] for array fields. Never guess.
4. The "summary" field must be 2-3 sentences maximum. It must be strictly factual and based only on what is written in the resume.
5. The "skills" field must be a flat array of strings taken directly from the resume. Do not add skills not listed.
6. The "achievements" field must be a flat array of strings — only include quantifiable or explicitly stated achievements from the resume.
7. For "contact", only populate sub-fields that are explicitly present. Leave all others as empty strings.

REQUIRED JSON SCHEMA (return this exact structure):
{{
  "name": "",
  "headline": "",
  "summary": "",
  "skills": [],
  "education": [
    {{"degree": "", "institution": "", "year": ""}}
  ],
  "experience": [
    {{"title": "", "company": "", "dates": "", "description": ""}}
  ],
  "projects": [
    {{"title": "", "description": "", "technologies": []}}
  ],
  "achievements": [],
  "contact": {{
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": ""
  }}
}}

RESUME TEXT:
{cleaned_text}"""


# ---------------------------------------------------------------------------
# Task 2 & 3 — Defensive JSON parsing
# ---------------------------------------------------------------------------
def _strip_markdown_fences(raw: str) -> str:
    """
    Removes ```json ... ``` or ``` ... ``` wrappers Gemini sometimes adds
    despite being told not to. Also strips stray leading/trailing whitespace.
    """
    # Pattern: optional ```json or ``` at start, optional ``` at end
    stripped = raw.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _fill_defaults(data: dict) -> dict:
    """
    Merges parsed data against schema defaults so every key the template
    expects is always present. Fills missing nested list item keys too.
    Raises nothing — defensive by design.
    """
    result = dict(_SCHEMA_DEFAULTS)

    # Scalar fields only — achievements handled separately as a typed list below
    for key in ("name", "headline", "summary"):
        if key in data and data[key] is not None:
            result[key] = data[key]

    if "skills" in data and isinstance(data["skills"], list):
        result["skills"] = [str(s) for s in data["skills"] if s]

    if "achievements" in data and isinstance(data["achievements"], list):
        result["achievements"] = [str(a) for a in data["achievements"] if a]

    # Education
    if "education" in data and isinstance(data["education"], list):
        result["education"] = [
            {**_EDUCATION_DEFAULTS, **{k: v for k, v in item.items() if k in _EDUCATION_DEFAULTS}}
            for item in data["education"]
            if isinstance(item, dict)
        ]

    # Experience
    if "experience" in data and isinstance(data["experience"], list):
        result["experience"] = [
            {**_EXPERIENCE_DEFAULTS, **{k: v for k, v in item.items() if k in _EXPERIENCE_DEFAULTS}}
            for item in data["experience"]
            if isinstance(item, dict)
        ]

    # Projects
    if "projects" in data and isinstance(data["projects"], list):
        result["projects"] = []
        for item in data["projects"]:
            if not isinstance(item, dict):
                continue
            proj = dict(_PROJECT_DEFAULTS)
            proj["title"] = item.get("title", "")
            proj["description"] = item.get("description", "")
            techs = item.get("technologies", [])
            proj["technologies"] = [str(t) for t in techs if t] if isinstance(techs, list) else []
            result["projects"].append(proj)

    # Contact (nested dict) — sanitize URL fields to block javascript: XSS
    if "contact" in data and isinstance(data["contact"], dict):
        contact_defaults = dict(_SCHEMA_DEFAULTS["contact"])
        for k, v in data["contact"].items():
            if k not in contact_defaults or v is None:
                continue
            if k in ("linkedin", "github"):  # Fix #4: enforce https-only URLs
                contact_defaults[k] = _safe_url(v)
            else:
                contact_defaults[k] = v
        result["contact"] = contact_defaults

    return result


def _parse_gemini_response(raw: str) -> dict:
    """
    Strips markdown fences, parses JSON, fills schema defaults.

    Raises:
        ValueError: if json.loads() fails entirely (app.py catches this as
                    Exception and returns HTTP 500 — do not swallow silently).
    """
    cleaned = _strip_markdown_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON that could not be parsed. "
            f"Parser error: {exc}. "
            f"Raw response (first 300 chars): {raw[:300]!r}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object from Gemini, got {type(data).__name__}. "
            f"Raw response (first 300 chars): {raw[:300]!r}"
        )

    return _fill_defaults(data)


# ---------------------------------------------------------------------------
# Task 4 — HTML rendering (public interface consumed by app.py)
# ---------------------------------------------------------------------------
_TEMPLATE_MAP = {
    1: "template_1.html",
    2: "template_2.html",
    3: "template_3.html",
    4: "template_4.html",
}


def build_portfolio(gemini_raw_response: str, template_num: int = 1) -> str:
    """
    Parses Gemini's JSON output and returns a rendered HTML string.

    This is the function app.py imports and calls directly.

    Args:
        gemini_raw_response: Raw text from get_gemini_response().
        template_num: Which portfolio template to render (1-4). Defaults to 1.

    Returns:
        Complete HTML page as a string.

    Raises:
        ValueError: If Gemini's response cannot be parsed as JSON.
                    app.py wraps this call in try/except and returns HTTP 500.
    """
    parsed = _parse_gemini_response(gemini_raw_response)
    template_file = _TEMPLATE_MAP.get(template_num, "template_1.html")
    
    # Read the CSS file so we can inline it
    from flask import current_app
    import os
    css_filename = f"template{template_num}.css"
    css_path = os.path.join(current_app.static_folder, css_filename)
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            parsed["inline_css"] = f.read()
    except FileNotFoundError:
        pass  # Fix #6: CSS file missing — templates have fallback <link> tags

    return render_template(template_file, **parsed)
