from flask import Flask, jsonify, request
import yfinance as yf
import os
import time
import re
from dotenv import load_dotenv
import google.generativeai as genai
import google.api_core.exceptions
from supabase import create_client

# ================= INIT =================

load_dotenv()

app = Flask(__name__)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemma-3-1b-it")
model = genai.GenerativeModel(MODEL_NAME)

# ================= STOCK API =================

TIMEFRAMES = {
    "1d": "1d",
    "1w": "7d",
    "1m": "1mo",
    "3m": "3mo",
    "1y": "1y"
}

@app.route("/")
def home():
    return "FinanceGPT API Running 🚀"

@app.route("/stock/<ticker>")
def get_stock(ticker):
    timeframe = request.args.get("range", "1m")
    period = TIMEFRAMES.get(timeframe, "1mo")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return jsonify({
                "ticker": ticker,
                "data": [],
                "message": "No data available"
            })

        data = [
            {"date": str(i.date()), "close": float(r["Close"])}
            for i, r in hist.iterrows()
        ]

        return jsonify({"ticker": ticker, "data": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= CHATBOT =================

global_user_name = None

def extract_user_name(question):
    match = re.search(r"i am ([a-zA-Z]+)", question, re.IGNORECASE)
    return match.group(1) if match else None


def get_user_id(token):
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        return None


def load_history(user_id):
    res = supabase.table("chat_history") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=False) \
        .limit(10) \
        .execute()

    return res.data if res.data else []


def save_chat(user_id, user_input, bot_response):
    supabase.table("chat_history").insert({
        "user_id": user_id,
        "user_message": user_input,
        "bot_response": bot_response
    }).execute()


def get_response(question, user_id):
    global global_user_name

    try:
        user_name = extract_user_name(question)
        if user_name:
            global_user_name = user_name.capitalize()
            return f"Hello {global_user_name}, how can I help you?"

        history = load_history(user_id)

        history_text = "\n".join([
            f"User: {row['user_message']}\nFinanceGPT: {row['bot_response']}"
            for row in history
        ])

        prompt = f"""
You are FinanceGPT, a financial assistant.

Chat history:
{history_text}

User: {question}
FinanceGPT:
"""

        print("🚀 Prompt sending...")

        res = model.generate_content(prompt)

        print("📦 RAW GEMINI RESPONSE:", res)

        # 🔥 SAFE EXTRACTION (NO CRASH)
        text = None

        if hasattr(res, "text") and res.text:
            text = res.text

        elif hasattr(res, "candidates") and res.candidates:
            cand = res.candidates[0]

            if hasattr(cand, "content") and cand.content:
                parts = cand.content.parts
                if parts and hasattr(parts[0], "text"):
                    text = parts[0].text

        if not text:
            return f"❌ Gemini returned empty response.\nRaw: {str(res)}"

        save_chat(user_id, question, text)

        return text

    except Exception as e:
        import traceback
        full_error = traceback.format_exc()
        print("🔥 FULL ERROR:\n", full_error)

        return f"❌ ERROR OCCURRED:\n{str(e)}"    
        
@app.route("/ask", methods=["POST"])
def ask():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "No auth"}), 401

    token = auth_header.split(" ")[1]
    user_id = get_user_id(token)

    if not user_id:
        return jsonify({"error": "Invalid user"}), 401

    data = request.get_json()
    question = data.get("question", "").strip()

    response = get_response(question, user_id)

    return jsonify({"response": response})


# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)