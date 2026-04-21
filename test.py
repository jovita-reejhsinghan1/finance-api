import requests
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# 🔗 CONFIG
BASE_URL = "https://finance-api-zngc.onrender.com"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

AUTH_URL = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

# 🔐 LOGIN FUNCTION
def login():
    print("🔐 Login to FinanceGPT\n")

    email = "d2024.jovita.reejhsinghani@ves.ac.in"
    password = "abcd1234"

    res = requests.post(
        AUTH_URL,
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": email,
            "password": password
        }
    )

    if res.status_code != 200:
        print("❌ Login failed:", res.text)
        return None

    data = res.json()
    token = data.get("access_token")

    print("✅ Login successful\n")
    return token


# 💬 CHAT FUNCTION
def chat(token):
    print("💬 FinanceGPT Terminal Chat (type 'exit' to quit)\n")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    while True:
        q = input("You: ")

        if q.lower() == "exit":
            break

        res = requests.post(
            f"{BASE_URL}/ask",
            json={"question": q},
            headers=headers
        )

        if res.status_code == 200:
            print("Bot:", res.json().get("response"))
        else:
            print("❌ Error:", res.text)


# 🚀 RUN
if __name__ == "__main__":
    token = login()

    if token:
        chat(token)