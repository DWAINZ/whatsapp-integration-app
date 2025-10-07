from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# === Load environment variables ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "dwainz_verify")  # default for safety
WABA_ID = os.getenv("WABA_ID")  # optional

API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"


# === Root route ===
@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"


# === Webhook Verification (GET) & Message Handling (POST) ===
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- 1️⃣ Verification Step (Meta GET Request) ---
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            print(f"❌ Verification token mismatch: got '{token}', expected '{VERIFY_TOKEN}'")
            return "Verification token mismatch", 403

    # --- 2️⃣ Handle Incoming WhatsApp Messages (Meta POST Request) ---
    elif request.method == "POST":
        data = request.get_json()
        print("📩 Incoming message data:", data)

        try:
            changes = data["entry"][0]["changes"][0]
            value = changes["value"]
            messages = value.get("messages", [])

            for msg in messages:
                sender = msg["from"]
                text = msg["text"]["body"] if "text" in msg else None

                # Skip echoes or non-user messages
                if "statuses" in value or sender == PHONE_NUMBER_ID:
                    continue

                print(f"💬 New message from {sender}: {text}")

                # --- Auto-reply logic ---
                reply_text = "Hello 👋, this is an automated response from D’wainz Integration App!"
                send_whatsapp_message(sender, reply_text)

        except Exception as e:
            print("⚠️ Error handling webhook:", e)

        return jsonify(status="received"), 200


# === Function to Send WhatsApp Messages ===
def send_whatsapp_message(recipient, text):
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"📤 Auto-reply sent to {recipient}: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send message to {recipient}: {e}")


# === Manual Send Endpoint (for testing with cURL/Postman) ===
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    to = data.get('to')
    message = data.get('message')

    if not to or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    send_whatsapp_message(to, message)
    return jsonify({"status": "sent"}), 200


# === App Runner ===
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
