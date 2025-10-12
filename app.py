from flask import Flask, request, jsonify
import requests
import os
import datetime
import sys
import pytz
import psycopg
from config import Config

app = Flask(__name__)
# -------------------------------------------
# CONFIGURATION
# -------------------------------------------
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# -------------------------------------------
# UTILITIES
# -------------------------------------------
class LogColors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

def get_timestamp():
    """Return current Nigerian timestamp."""
    return datetime.datetime.now(pytz.timezone("Africa/Lagos"))

def log_info(message, color=LogColors.BLUE):
    """Prints timestamped colored log lines with flush for Render."""
    timestamp = get_timestamp().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"{color}[{timestamp}] {message}{LogColors.RESET}\n")
    sys.stdout.flush()


# -------------------------------------------
# ROUTES
# -------------------------------------------
@app.route("/", methods=["GET"])
def home():
    """Render-friendly home route."""
    return jsonify({
        "status": "✅ WhatsApp Integration Active",
        "message": "Your bot is running successfully 🚀",
        "time": get_timestamp().strftime("%Y-%m-%d %H:%M:%S")
    }), 200

# -------------------------------------------
# ROUTES TO TEST DATABASE CONNECTION
# -------------------------------------------
@app.route("/test-db", methods=["GET"])
def test_database():
    """Test database connection"""
    try:
        # Simple connection with new psycopg
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        log_info(f"✅ Database connected: {db_version[0]}", LogColors.GREEN)
        return jsonify({
            "status": "Database connected successfully", 
            "version": db_version[0]
        }), 200
        
    except Exception as e:
        log_info(f"❌ Database connection failed: {e}", LogColors.RED)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------
# WEBHOOK VERIFICATION
# -------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        log_info("✅ Webhook verified successfully.", LogColors.GREEN)
        return challenge, 200
    else:
        log_info("❌ Webhook verification failed.", LogColors.RED)
        return "Verification failed", 403

# -------------------------------------------
# HANDLE INCOMING WHATSAPP MESSAGES
# -------------------------------------------
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()

    if not data:
        log_info("⚠️ No data in POST payload", LogColors.RED)
        return jsonify({"status": "no data"}), 200

    # Ignore non-message updates
    if "messages" not in str(data):
        return jsonify({"status": "ignored"}), 200

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    from_number = message.get("from")
                    msg_body = message.get("text", {}).get("body", "").strip()

                    log_info(f"💬 Message from {from_number}: {msg_body}", LogColors.YELLOW)

                    # Prepare custom reply
                    local_time = get_timestamp().strftime("%I:%M %p")
                    if msg_body.lower() == "hi":
                        reply_text = f"👏 Hello!\nYou said “Hi” — received at {local_time}"
                    else:
                        reply_text = f"Hi 👋, you said “{msg_body}” — received at {local_time}"

                    send_whatsapp_message(from_number, reply_text)
                    log_info(f"✅ Message sent successfully to {from_number}", LogColors.GREEN)

        return jsonify({"status": "message processed"}), 200

    except Exception as e:
        log_info(f"❌ Error processing message: {e}", LogColors.RED)
        return jsonify({"error": str(e)}), 500

# -------------------------------------------
# SEND MESSAGE FUNCTION
# -------------------------------------------
def send_whatsapp_message(to_number, message):
    try:
        url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
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
        else:
            log_info(f"📤 API responded OK: {response.text}", LogColors.GREEN)

    except Exception as e:
        log_info(f"❌ Failed to send message: {e}", LogColors.RED)

# -------------------------------------------
# RUN APP
# -------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    log_info(f"🚀 Server starting on port {port}...", LogColors.BLUE)
    app.run(host="0.0.0.0", port=port)
