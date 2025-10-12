from flask import Flask, request, jsonify
import requests
import os
import datetime
import sys

app = Flask(__name__)

# WhatsApp credentials from environment variables
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Nigerian timezone offset (+1 hour)
def get_timestamp():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=1)

# Color and emoji log system
class LogColors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

def log_info(message, color=LogColors.BLUE):
    timestamp = get_timestamp().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"{color}[{timestamp}] {message}{LogColors.RESET}\n")
    sys.stdout.flush()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "WhatsApp Bot Running 🚀"}), 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    verify_token = os.getenv("VERIFY_TOKEN", "my_verify_token")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        log_info("Webhook verified successfully ✅", LogColors.GREEN)
        return challenge, 200
    else:
        log_info("Webhook verification failed ❌", LogColors.RED)
        return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()

    if data and "entry" in data:
        try:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        value = change.get("value", {})
                        messages = value.get("messages", [])
                        if messages:
                            for message in messages:
                                from_number = message["from"]
                                msg_body = message["text"]["body"] if "text" in message else ""
                                
                                log_info(f"💬 Message from {from_number}: {msg_body}", LogColors.YELLOW)
                                
                                send_whatsapp_message(from_number, f"Echo: {msg_body}")
                                log_info(f"✅ Message sent successfully to {from_number}", LogColors.GREEN)
            return jsonify({"status": "message processed"}), 200
        except Exception as e:
            log_info(f"❌ Error processing message: {e}", LogColors.RED)
            return jsonify({"error": str(e)}), 500

    log_info("⚠️ No message data found in request", LogColors.RED)
    return jsonify({"status": "no message"}), 200

def send_whatsapp_message(to_number, message):
    try:
        url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            log_info(f"⚠️ WhatsApp API error {response.status_code}: {response.text}", LogColors.RED)
    except Exception as e:
        log_info(f"❌ Failed to send message: {e}", LogColors.RED)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    log_info(f"🚀 Server starting on port {port}...", LogColors.BLUE)
    app.run(host="0.0.0.0", port=port)
