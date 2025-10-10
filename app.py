from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# === Load environment variables ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WABA_ID = os.getenv("WABA_ID")  # optional, for future use

API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

# === Helper: timestamp for Nigerian time ===
def ng_time():
    tz = pytz.timezone("Africa/Lagos")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# === Helper: color print ===
class color:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    END = "\033[0m"

# === Root route ===
@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"

# === Webhook route (GET + POST) ===
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print(f"{color.GREEN}[{ng_time()}] ✅ Webhook verified successfully!{color.END}")
            return challenge, 200
        else:
            print(f"{color.RED}[{ng_time()}] ❌ Verification token mismatch{color.END}")
            return "Verification token mismatch", 403

    elif request.method == 'POST':
        data = request.get_json()
        print(f"{color.BLUE}[{ng_time()}] 📩 Incoming webhook event{color.END}")

        try:
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})

            # Skip status updates
            if "statuses" in value:
                return "EVENT_RECEIVED", 200

            messages = value.get("messages")
            if not messages:
                return "EVENT_RECEIVED", 200

            msg = messages[0]
            sender = msg["from"]
            text = msg.get("text", {}).get("body", "")
            print(f"{color.GREEN}[{ng_time()}] 💬 Message from {sender}: {text}{color.END}")

            # ✅ Auto reply
            reply_text = f"Hello 👋 I got your message: '{text}'"
            send_message(sender, reply_text)

        except Exception as e:
            print(f"{color.RED}[{ng_time()}] ⚠️ Error: {e}{color.END}")

        return "EVENT_RECEIVED", 200

# === Helper function to send a message ===
def send_message(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"{color.BLUE}[{ng_time()}] ➡️ Sent message response: {response.status_code}, {response.text}{color.END}")
    return response

# === Manual message sending endpoint ===
@app.route('/send', methods=['POST'])
def manual_send():
    data = request.get_json()
    to = data.get('to')
    message = data.get('message')

    if not to or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    response = send_message(to, message)
    return jsonify(response.json()), response.status_code

# === Run the app ===
if __name__ == "__main__":
    print("\n🌍 Starting WhatsApp Integration App...")
    print("Loaded Environment Variables:")
    print(f"  ✅ PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
    print(f"  ✅ WABA_ID: {WABA_ID if WABA_ID else 'Not set'}")
    print(f"  ✅ VERIFY_TOKEN: {VERIFY_TOKEN}")
    print(f"  ✅ ACCESS_TOKEN: {'Loaded' if ACCESS_TOKEN else 'Missing!'}")
    print("--------------------------------------------------\n")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
