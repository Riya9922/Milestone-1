import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY")
print(f"Key found: {key[:5]}...{key[-5:]}" if key else "Key NOT found")

if key:
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
