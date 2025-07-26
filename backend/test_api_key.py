import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from app.config import settings
import google.generativeai as genai
def test_api_key():
    try:
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello, the API key is working!'")
        print("✅ SUCCESS: Google Gemini API key is working!")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print("❌ ERROR: Google Gemini API key is not working!")
        print(f"Error details: {e}")
        print("\nPlease check:")
        print("1. You have set GOOGLE_API_KEY in backend/.env")
        print("2. The API key is valid (get one from https://aistudio.google.com/)")
        print("3. The API key has the correct permissions")
        return False
if __name__ == "__main__":
    print("Testing Google Gemini API key...")
    print(f"Current API key: {settings.google_api_key[:10]}..." if settings.google_api_key else "No API key set")
    print()
    if not settings.google_api_key or settings.google_api_key == "your_google_api_key_here":
        print("❌ No valid API key found in .env file!")
        print("Please set GOOGLE_API_KEY in backend/.env")
        sys.exit(1)
    success = test_api_key()
    sys.exit(0 if success else 1)