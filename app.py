from flask import Flask, request, jsonify
import requests
import datetime
import pytz
import logging
from colorama import Fore, Style

app = Flask(__name__)

# -------------------------------------------
# CONFIGURATION
# -------------------------------------------
import os

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


# -------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------
def log_info(message):
    """Colored log with timestamp in Nigerian time."""
    naija_time = datetime.datetime.now(pytz.timezone('Africa/Lagos')).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Fore.CYAN}[{naija_time}] {Style.RESET_ALL}{message}")


def send_whatsapp_message(to, text):
    """Send a message via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        log_info(f"{Fore.GREEN}✅ Message sent successfully to {to}{Style.RESET_ALL}")
    else:
        log_info(f"{Fore.RED}❌ Failed to send message: {response.text}{Style.RESET_ALL}")


# -------------------------------------------
# WEBHOOK VERIFICATION (GET)
# -------------------------------------------
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        log_info("✅ Webhook verified successfully.")
        return challenge, 200
    else:
        log_info("❌ Webhook verification failed.")
        return "Verification failed", 403


# -------------------------------------------
# WEBHOOK EVENT HANDLER (POST)
# -------------------------------------------
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    log_info(f"📩 Received webhook: {data}")

    if data and data.get("entry"):
        for entry in data["entry"]:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                if messages:
                    message = messages[0]
                    phone_number = message["from"]
                    msg_body = message["text"]["body"]

                    log_info(f"💬 Incoming message from {phone_number}: {msg_body}")

                    # Send an automatic reply
                    reply_text = f"Hi 👋, you said: '{msg_body}' — received at {datetime.datetime.now(pytz.timezone('Africa/Lagos')).strftime('%I:%M %p')}"
                    send_whatsapp_message(phone_number, reply_text)
    return jsonify({"status": "received"}), 200


# -------------------------------------------
# MAIN ENTRY POINT
# -------------------------------------------
if __name__ == '__main__':
    log_info("🚀 Server starting on port 10000...")
    app.run(host='0.0.0.0', port=10000)
