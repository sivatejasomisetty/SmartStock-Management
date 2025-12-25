import os
from dotenv import load_dotenv
import google.generativeai as genai

from app.ml.alerts import generate_alerts
from app.ml.predictor import predict_units

# Load env
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY='AIzaSyAzJdwiLfkTGXazhYKDZPbW6mLlvfMhbgE'

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not loaded")

print("🔑 Gemini API key loaded successfully")

genai.configure(api_key=API_KEY)

# ✅ Working model
model = genai.GenerativeModel("gemini-2.5-flash")


def chatbot_response(message: str):
    try:
        msg = message.lower()

        if "understock" in msg or "alert" in msg:
            alerts = generate_alerts()
            context = f"Inventory alerts: {alerts}"

        elif "predict" in msg or "demand" in msg:
            prediction = predict_units("S001", "P0001")
            context = f"Demand prediction: {prediction}"

        else:
            context = "General inventory assistance."

        prompt = f"""
You are SmartStock AI, an inventory management assistant.

User question:
{message}

System data:
{context}

Answer clearly and concisely.
"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print("🔥 Gemini error:", e)
        return "Sorry, the chatbot is currently unavailable."
