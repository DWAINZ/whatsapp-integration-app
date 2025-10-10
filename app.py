from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# === Load environment variables ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WABA_ID = os.getenv("WABA_ID")

API_URL = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

# === Root route ===
@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"

# === Webhook route (GET + POST) ===
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # ✅ Verification handshake with Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            print("❌ Verification token mismatch")
            return "Verification token mismatch", 403

    elif request.method == 'POST':
        # ✅ Handle incoming webhook messages
        try:
            data = request.get_json()
            print("\n📩 Incoming message payload:")
            print(json.dumps(data, indent=2))

            # Check if message exists in payload
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                print("⚠️ No 'messages' field found in payload.")
                return jsonify({"status": "no_messages"}), 200

            # Extract sender and text
            msg = messages[0]
            sender = msg.get("from")
            text = msg.get("text", {}).get("body", "")

            print(f"💬 Message from {sender}: {text}")

            if sender and text:
                reply_text = f"Hello 👋! I got your message: “{text}”"
                send_message(sender, reply_text)

        except Exception as e:
            print(f"⚠️ Error handling incoming message: {e}")

        return jsonify({"status": "event_received"}), 200

# === Helper function to send a WhatsApp message ===
def send_message(to, text):
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

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print("➡️ Sent message response:", response.status_code, response.text)
        return response
    except Exception as e:
        print(f"⚠️ Failed to send message: {e}")

# === Manual message sending endpoint (optional) ===
@app.route('/send', methods=['POST'])
def manual_send():
    data = request.get_json()
    to = data.get('to')
    message = data.get('message')

    if not to or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    response = send_message(to, message)
    return jsonify({"status": "sent"}), 200

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
