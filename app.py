from flask import Flask, request, jsonify
import requests
import datetime
import pytz
import os
import logging
from colorama import Fore, Style

# ----------------------------------------------------
# APP SETUP
# ----------------------------------------------------
app = Flask(__name__)

# Environment Variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def log_info(message):
    """Logs with Nigerian timestamp and color."""
    naija_time = datetime.datetime.now(pytz.timezone('Africa/Lagos')).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Fore.CYAN}[{naija_time}] {Style.RESET_ALL}{message}")

# ----------------------------------------------------
# ROOT ROUTE (FIXES 404 ON WEB)
# ----------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    """Homepage for testing Render deployment."""
    return "<h3>✅ WhatsApp Integration Webhook is Live!</h3><p>App running successfully on Render.</p>", 200

# ----------------------------------------------------
# WEBHOOK VERIFICATION
# ----------------------------------------------------
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

# ----------------------------------------------------
# HANDLE INCOMING WHATSAPP MESSAGES
# ----------------------------------------------------
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "no data"}), 200

    # Ignore non-message updates (status, delivery reports)
    if "messages" not in str(data):
        return jsonify({"status": "ignored"}), 200

    log_info(f"📩 Incoming webhook payload received.")

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    phone_number = message.get("from")
                    msg_body = message.get("text", {}).get("body", "")
                    log_info(f"💬 Message from {phone_number}: {msg_body}")

                    # Send reply
                    reply_text = f"Hi 👋, you said: '{msg_body}' — received at {datetime.datetime.now(pytz.timezone('Africa/Lagos')).strftime('%I:%M %p')}"
                    send_whatsapp_message(phone_number, reply_text)
    except Exception as e:
        log_info(f"{Fore.RED}⚠️ Error processing webhook: {e}{Style.RESET_ALL}")

    return jsonify({"status": "received"}), 200

# ----------------------------------------------------
# SEND WHATSAPP MESSAGE FUNCTION
# ----------------------------------------------------
def send_whatsapp_message(to, text):
    """Send a text message via WhatsApp Cloud API."""
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

# ----------------------------------------------------
# RUN APP
# ----------------------------------------------------
if __name__ == '__main__':
    log_info("🚀 Server starting on port 10000...")
    app.run(host='0.0.0.0', port=10000)
