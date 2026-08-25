"""
app.py
Owns: Flask routes + upload handling. Hands off cleaned text to Gemini,
then hands the raw Gemini response to Dev 2's parsing/rendering function.

Flow:
  GET  /          -> upload form (index.html)
  POST /parse     -> clean text -> Gemini -> return structured JSON (Review screen)
  POST /render    -> accept JSON + template choice -> return rendered HTML (Preview)
  POST /generate  -> parse + render shortcut (legacy / tests)
"""

import os
from flask import Flask, request, render_template, jsonify, Response

from gemini_client import get_gemini_response, GeminiRequestError

# --- Dev 2's functions (portfolio_builder.py) ----------------------------
from portfolio_builder import (
    build_prompt,            # owns the Gemini prompt wording
    build_portfolio,         # parse + render in one shot (legacy /generate)
    _parse_gemini_response,  # used by /parse
    _fill_defaults,          # used by /render
    _TEMPLATE_MAP,           # template id -> filename map
)
# -------------------------------------------------------------------------

ALLOWED_TEMPLATES = {1, 2, 3, 4}
MIN_RESUME_LENGTH = 50

# Calculate absolute paths to the frontend directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(base_dir, 'frontend')

app = Flask(
    __name__,
    template_folder=os.path.join(frontend_dir, 'templates'),
    static_folder=os.path.join(frontend_dir, 'static')
)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # Fix #3: 1 MB upload limit — prevents DoS via huge file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_resume_text(raw_text: str) -> str:
    """Strip whitespace, drop blank lines, collapse repeated spaces."""
    lines = [line.strip() for line in raw_text.splitlines()]
    non_blank_lines = [line for line in lines if line]
    collapsed = [" ".join(line.split()) for line in non_blank_lines]
    return "\n".join(collapsed)


def _extract_raw_text(req) -> str:
    """Pull resume text from either a file upload or a pasted text field."""
    raw_text = ""
    uploaded_file = req.files.get("resume")
    if uploaded_file and uploaded_file.filename:
        try:
            raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    if not raw_text or len(raw_text.strip()) < MIN_RESUME_LENGTH:
        pasted = req.form.get("resume_text", "").strip()
        if pasted:
            raw_text = pasted

    return raw_text


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/parse", methods=["POST"])
def parse():
    """
    Step 1 of the 2-step flow.
    Sends resume text to Gemini and returns structured JSON.
    The frontend uses this to populate the Review screen.
    """
    raw_text = _extract_raw_text(request)

    if not raw_text:
        return jsonify({"error": "No resume uploaded"}), 400

    if len(raw_text.strip()) < MIN_RESUME_LENGTH:
        return jsonify({"error": "Resume content too short to process"}), 400

    cleaned_text = clean_resume_text(raw_text)

    if len(cleaned_text) < MIN_RESUME_LENGTH:
        return jsonify({"error": "Resume content too short to process"}), 400

    prompt = build_prompt(cleaned_text)
    try:
        gemini_raw_response = get_gemini_response(prompt)
    except GeminiRequestError as e:
        return jsonify({"error": f"Gemini request failed: {e}"}), 502

    try:
        parsed = _parse_gemini_response(gemini_raw_response)
    except ValueError as e:
        return jsonify({"error": f"Failed to parse Gemini response: {e}"}), 500

    return jsonify(parsed)


@app.route("/render", methods=["POST"])
def render_portfolio():
    """
    Step 2 of the 2-step flow.
    Accepts the (possibly user-reviewed) JSON + template number,
    renders the Jinja2 template, and returns HTML for the Preview iframe.
    No page navigation occurs — the browser stays on the SPA.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        template_num = int(data.get("template", 1))
        if template_num not in ALLOWED_TEMPLATES:
            template_num = 1
    except (ValueError, TypeError):
        template_num = 1

    parsed = _fill_defaults(data)
    template_file = _TEMPLATE_MAP.get(template_num, "template_1.html")

    # Read the CSS file so we can inline it
    css_filename = f"template{template_num}.css"
    css_path = os.path.join(app.static_folder, css_filename)
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            parsed["inline_css"] = f.read()
    except Exception:
        pass

    try:
        portfolio_html = render_template(template_file, **parsed)
    except Exception as e:
        return jsonify({"error": f"Failed to render portfolio: {e}"}), 500

    return Response(portfolio_html, mimetype="text/html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Legacy shortcut: parse + render in a single POST.
    Used by tests or direct API callers.
    """
    raw_text = _extract_raw_text(request)

    if not raw_text:
        return jsonify({"error": "No resume uploaded"}), 400

    if len(raw_text.strip()) < MIN_RESUME_LENGTH:
        return jsonify({"error": "Resume content too short to process"}), 400

    try:
        template_num = int(request.form.get("template", 1))
        if template_num not in ALLOWED_TEMPLATES:
            template_num = 1
    except (ValueError, TypeError):
        template_num = 1

    cleaned_text = clean_resume_text(raw_text)

    if len(cleaned_text) < MIN_RESUME_LENGTH:
        return jsonify({"error": "Resume content too short to process"}), 400

    prompt = build_prompt(cleaned_text)
    try:
        gemini_raw_response = get_gemini_response(prompt)
    except GeminiRequestError as e:
        return jsonify({"error": f"Gemini request failed: {e}"}), 502

    try:
        portfolio_html = build_portfolio(gemini_raw_response, template_num=template_num)
    except Exception as e:
        return jsonify({"error": f"Failed to build portfolio: {e}"}), 500

    return portfolio_html


if __name__ == "__main__":
    app.run(debug=True)
