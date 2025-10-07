from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# === Load environment variables ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WABA_ID = os.getenv("WABA_ID")  # Optional, for future use

API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"


# === Root route ===
@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"


# === Webhook Verification (for Meta) ===
@app.route('/webhook', methods=['GET'])
def verify_token():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return challenge, 200
    else:
        print("❌ Verification token mismatch")
        return "Verification token mismatch", 403


# === Handle Incoming Messages (POST) ===
@app.route('/webhook', methods=['POST'])
def webhook_received():
    data = request.get_json()
    print("📩 Incoming message data:", data)

    # Future logic can go here for automated responses or routing
    return "EVENT_RECEIVED", 200


# === Send Message Endpoint (for manual testing) ===
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    to = data.get('to')
    message = data.get('message')

    if not to or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    return jsonify(response.json()), response.status_code


# === Run the app ===
if __name__ == "__main__":
    # Print environment variable summary for debugging
    print("\n🌍 Starting WhatsApp Integration App...")
    print("Loaded Environment Variables:")
    print(f"  ✅ PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
    print(f"  ✅ WABA_ID: {WABA_ID if WABA_ID else 'Not set'}")
    print(f"  ✅ VERIFY_TOKEN: {VERIFY_TOKEN}")
    print(f"  ✅ ACCESS_TOKEN: {'Loaded' if ACCESS_TOKEN else 'Missing!'}")
    print("--------------------------------------------------\n")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
