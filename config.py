import os
import google.generativeai as genai

# Load environment variables from .env if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

try:
    if api_key:
        genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
except Exception as e:
    print(f"Warning: Gemini API initialization error: {e}")
    model = None