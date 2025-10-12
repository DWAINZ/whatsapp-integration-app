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
# INITIALIZE DATABASE ROUTE
# -------------------------------------------
@app.route("/init-db", methods=["GET"])
def initialize_database_route():
    """Initialize database tables"""
    if init_database():
        return jsonify({"status": "Database tables created successfully"}), 200
    else:
        return jsonify({"error": "Database initialization failed"}), 500

# -------------------------------------------
# DATABASE INITIALIZATION
# -------------------------------------------
def init_database():
    """Create all necessary tables"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Table 1: Staff (Client Team & Vendor Team)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                phone_number VARCHAR(20) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('client_team', 'vendor_team', 'admin')),
                display_name VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Clients (with temporary/permanent status)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                encrypted_id VARCHAR(20) UNIQUE NOT NULL,
                real_phone_number VARCHAR(20) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'temporary' CHECK (status IN ('temporary', 'permanent')),
                first_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_deals INTEGER DEFAULT 0
            )
        """)
        
        # Table 3: Vendors (pre-registered by admin)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id SERIAL PRIMARY KEY,
                encrypted_id VARCHAR(20) UNIQUE NOT NULL,
                real_phone_number VARCHAR(20) UNIQUE NOT NULL,
                vendor_name VARCHAR(100),
                category VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 4: Conversations (Client-side)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id),
                assigned_staff_id INTEGER REFERENCES staff(id),
                status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'pending_vendor')),
                current_deal_description TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                auto_close_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 5: Internal Conversations (Client Team ↔ Vendor Team)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internal_conversations (
                id SERIAL PRIMARY KEY,
                client_conversation_id INTEGER REFERENCES conversations(id),
                client_staff_id INTEGER REFERENCES staff(id),
                vendor_staff_id INTEGER REFERENCES staff(id),
                vendor_id INTEGER REFERENCES vendors(id),
                status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'quote_received')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 6: Messages (All messages storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER,
                internal_conversation_id INTEGER,
                from_number VARCHAR(20),
                to_number VARCHAR(20),
                content TEXT,
                message_type VARCHAR(20) DEFAULT 'text',
                direction VARCHAR(10) CHECK (direction IN ('incoming', 'outgoing')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                encrypted_sender_id VARCHAR(20),
                encrypted_receiver_id VARCHAR(20)
            )
        """)
        
        # Table 7: Staff-Vendor Permissions (Admin controls)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_vendor_permissions (
                id SERIAL PRIMARY KEY,
                staff_id INTEGER REFERENCES staff(id),
                vendor_id INTEGER REFERENCES vendors(id),
                can_access BOOLEAN DEFAULT TRUE,
                assigned_by INTEGER REFERENCES staff(id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_info("✅ Database tables created successfully!", LogColors.GREEN)
        return True
        
    except Exception as e:
        log_info(f"❌ Database initialization failed: {e}", LogColors.RED)
        return False

# -------------------------------------------
# INITIALIZE DATABASE ON STARTUP
# -------------------------------------------
@app.before_first_request
def initialize_database():
    init_database()

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
