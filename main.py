import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running flawlessly!"

def run():
    # Render ka temporary port uthane ke liye
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# Isse web server alag se background thread mein chalega
Thread(target=run).start()

# --- ISKE NEECHE AAPKA PURANA BOT KA CODE AAYEGA ---
# Jaise: bot.polling() ya application.run_polling()
import requests
import json
import time

# ===== CONFIGURATION =====
# !!!!! BAS YEH EK LINE MEIN TOKEN DAALO !!!!!
BOT_TOKEN = "8693148816:AAGtEdT7kI3UXMYcXahqDeATa5AdGEA3br0"  # <--- SIRF YAHAN TOKEN DAALO
EXTERNAL_API_URL = "https://san-ju.vercel.app/userid/"

# ===== TELEGRAM BOT API BASE URL =====
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===== KEYBOARD SETUP =====
KEYBOARD = {
    "keyboard": [
        [{"text": "📱 Phone Lookup"}]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False
}

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
        
    try:
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
    return None
def lookup_phone(phone_number):
    try:
        response = requests.get(f"{EXTERNAL_API_URL}?phone={phone_number}")
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"raw_response": response.text}
    
    except Exception as e:
        return {"error": str(e)}

def is_valid_phone(text):
    cleaned = text.replace(" ", "").replace("-", "").replace("+", "")
    
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    
    if len(cleaned) == 10 and cleaned.isdigit():
        return True
    return False

def format_response(data):
    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    return f"<pre>{formatted_json}</pre>"

import requests

# --- APNI DETAILS YAHAN DAALEIN ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL_ID = "-1002091456364"  # Apni -100 wali Channel ID
CHANNEL_URL = "https://t.me/+pDQ_FnUdGD00Zjk1"

# --- HELPER FUNCTIONS ---
def send_message(chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_markup:
        params["reply_markup"] = str(reply_markup).replace("'", '"')
    requests.get(f"{BASE_URL}/sendMessage", params=params)

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    if offset: url += f"?offset={offset}"
    return requests.get(url).json()

# --- GATEKEEPER ---
def is_user_in_channel(user_id):
    params = {"chat_id": CHANNEL_ID, "user_id": user_id}
    response = requests.get(f"{BASE_URL}/getChatMember", params=params).json()
    if response.get("ok"):
        return response["result"]["status"] in ["member", "administrator", "creator"]
    return False

def handle_callback(callback_query):
    user_id = callback_query["from"]["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    requests.get(f"{BASE_URL}/answerCallbackQuery?callback_query_id={callback_query['id']}")
    
    if callback_query.get("data") == "verify":
        if is_user_in_channel(user_id):
            send_message(chat_id, "✅ Verified! Ab aap bot use kar sakte hain.")
        else:
            send_message(chat_id, "❌ Aapne channel join nahi kiya. Pehle join karein!")

# --- MESSAGE PROCESSOR ---
def process_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if not is_user_in_channel(user_id):
        markup = {"inline_keyboard": [[{"text": "CLICK HERE ✅", "url": CHANNEL_URL}],
                                      [{"text": "JOINED & VERIFY ✅", "callback_data": "verify"}]]}
        send_message(chat_id, "🚫 Access Denied! Bot use karne ke liye channel join karein.", reply_markup=markup)
        return

    text = message.get("text", "")
    if text == "/start":
        send_message(chat_id, "Welcome to the Phone Lookup Bot!")

# --- MAIN LOOP ---
offset = 0
while True:
    updates = get_updates(offset)
    if updates.get("result"):
        for update in updates["result"]:
            offset = update["update_id"] + 1
            if "callback_query" in update:
                handle_callback(update["callback_query"])
            elif "message" in update:
                process_message(update["message"])
    if text == "/start":
        welcome_message = (
            "👋 Welcome to the Phone Lookup Bot!\n\n"
            "I can help you look up information about phone numbers.\n"
            "Press the button below to get started."
        )
        send_message(chat_id, welcome_message, reply_markup=KEYBOARD)
        return

    if text == "📱 Phone Lookup":
        send_message(chat_id, "📞 Send 10 digit mobile number:")
        return

    if is_valid_phone(text):
        cleaned_number = text.replace(" ", "").replace("-", "").replace("+", "")
        if cleaned_number.startswith("91") and len(cleaned_number) == 12:
            cleaned_number = cleaned_number[2:]

        send_message(chat_id, "🔍 Looking up phone number...")
        try:
            full_url = f"https://san-ju.vercel.app/userid/{cleaned_number}"
            response = requests.get(full_url)
            if response.status_code == 200:
                api_response = response.json()
                formatted_message = format_response(api_response)
                send_message(chat_id, formatted_message, parse_mode="HTML")
            else:
                send_message(chat_id, "❌ Failed to get response from API. Please try again.")
        except Exception as e:
            send_message(chat_id, f"❌ Error fetching data: {e}")
    else:
        send_message(
            chat_id,
            "❌ Invalid input! Please send a valid 10-digit mobile number."
        )

def main():
    print("🤖 Bot is starting...")
    offset = None
    processed_updates = set()  # Purani requests ko yaad rakhne ke liye

    while True:
        try:
            updates = get_updates(offset)
            if updates and updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    u_id = update["update_id"]
                    offset = u_id + 1
                    
                    # Agar yeh update pehle hi process ho chuka hai, toh skip karo
                    if u_id in processed_updates:
                        continue
                        
                    processed_updates.add(u_id)
                    
                    # Set ko zyada bada hone se rokne ke liye clean-up
                    if len(processed_updates) > 100:
                        processed_updates.clear()
                    
                    if "message" in update:
                        process_message(update["message"])
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user.")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(5)
            
        time.sleep(0.5)
            
        time.sleep(0.5)
if __name__=="__main__":
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please set your BOT_TOKEN in the code!")
    else:
        main()
