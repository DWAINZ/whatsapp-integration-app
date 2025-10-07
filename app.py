from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# === Load environment variables ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"


# === Root route ===
@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"


# === Webhook Verification (for Meta) ===
@app.route('/webhook', methods=['GET'])
def verify_token():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification token mismatch", 403


# === Handle Incoming Messages (POST) ===
@app.route('/webhook', methods=['POST'])
def webhook_received():
    data = request.get_json()
    print("📩 Incoming message data:", data)

    # You can add logic here to respond automatically or log messages.
    return "EVENT_RECEIVED", 200


# === Send Message Endpoint (for testing manual sends) ===
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
