import sys
import os

# Append parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import model, api_key

try:
    if not api_key:
        print("No GEMINI_API_KEY detected in environment or .env file.")
    elif model is None:
        print("Model initialization failed.")
    else:
        response = model.generate_content("Hello! Say 'OK'")
        print("API Key works:", response.text)
except Exception as e:
    print("API Key error:", e)

