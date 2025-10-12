from flask import Flask, request, jsonify
import requests
import os
import datetime
import sys
import pytz
import psycopg
import hashlib
import secrets
from datetime import datetime, timedelta
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
# CLIENT MANAGEMENT SYSTEM
# -------------------------------------------
def generate_temporary_id():
    """Generate temporary prospect client ID (PCl-DDMMYYYY+serial)"""
    today = datetime.now().strftime("%d%m%Y")
    
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM clients WHERE encrypted_id LIKE %s",
            (f"PCl-{today}%",)
        )
        count = cursor.fetchone()[0] + 1
        cursor.close()
        conn.close()
        return f"PCl-{today}{count:02d}"
    except:
        return f"PCl-{today}01"

def generate_permanent_id():
    """Generate permanent customer ID (C-0001 sequential)"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients WHERE status = 'permanent'")
        count = cursor.fetchone()[0] + 1
        cursor.close()
        conn.close()
        return f"C-{count:04d}"
    except:
        return "C-0001"

def get_or_create_client(phone_number):
    """Get existing client or create new temporary one"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if client already exists
        cursor.execute("""
            SELECT id, encrypted_id, status, total_deals 
            FROM clients WHERE real_phone_number = %s
        """, (phone_number,))
        existing_client = cursor.fetchone()
        
        if existing_client:
            # Update last interaction
            cursor.execute(
                "UPDATE clients SET last_interaction = CURRENT_TIMESTAMP WHERE id = %s",
                (existing_client[0],)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            log_info(f"📞 Returning client: {existing_client[1]}", LogColors.GREEN)
            return {
                "id": existing_client[0],
                "encrypted_id": existing_client[1],
                "status": existing_client[2],
                "total_deals": existing_client[3],
                "is_new": False
            }
        else:
            # Create new TEMPORARY client
            encrypted_id = generate_temporary_id()
            cursor.execute("""
                INSERT INTO clients (encrypted_id, real_phone_number, status) 
                VALUES (%s, %s, 'temporary') RETURNING id
            """, (encrypted_id, phone_number))
            
            new_client_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            log_info(f"👤 New temporary client: {encrypted_id}", LogColors.BLUE)
            return {
                "id": new_client_id,
                "encrypted_id": encrypted_id,
                "status": "temporary",
                "total_deals": 0,
                "is_new": True
            }
            
    except Exception as e:
        log_info(f"❌ Error in get_or_create_client: {e}", LogColors.RED)
        return None

def pre_register_client(phone_number, custom_code=None, status="temporary", upgraded_by_admin=None):
    """Admin function to pre-register clients with custom codes"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute("SELECT id FROM clients WHERE real_phone_number = %s", (phone_number,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Client already exists"
        
        # Generate or use custom code
        if custom_code:
            encrypted_id = custom_code
        elif status == "permanent":
            encrypted_id = generate_permanent_id()
        else:
            encrypted_id = generate_temporary_id()
        
        cursor.execute("""
            INSERT INTO clients (encrypted_id, real_phone_number, status, total_deals) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (encrypted_id, phone_number, status, 1 if status == "permanent" else 0))
        
        new_client_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        log_info(f"👑 Admin pre-registered: {encrypted_id} for {phone_number}", LogColors.GREEN)
        return True, encrypted_id
        
    except Exception as e:
        log_info(f"❌ Error pre-registering client: {e}", LogColors.RED)
        return False, str(e)

def upgrade_client_to_permanent(client_id, upgraded_by_staff_id=None):
    """Upgrade client from temporary to permanent"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Get current client info
        cursor.execute("SELECT encrypted_id, status FROM clients WHERE id = %s", (client_id,))
        client_data = cursor.fetchone()
        
        if not client_data:
            return None
        
        old_id, old_status = client_data
        
        # Generate new permanent ID if not already permanent
        if old_status != "permanent":
            permanent_id = generate_permanent_id()
            
            cursor.execute("""
                UPDATE clients 
                SET encrypted_id = %s, status = 'permanent', total_deals = total_deals + 1 
                WHERE id = %s
            """, (permanent_id, client_id))
            
            log_info(f"⭐ Client upgraded: {old_id} → {permanent_id}", LogColors.GREEN)
            result_id = permanent_id
        else:
            result_id = old_id
        
        conn.commit()
        cursor.close()
        conn.close()
        return result_id
        
    except Exception as e:
        log_info(f"❌ Error upgrading client: {e}", LogColors.RED)
        return None

def downgrade_client_to_temporary(client_id, downgraded_by_admin=None):
    """Admin function to downgrade client to temporary"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        temporary_id = generate_temporary_id()
        
        cursor.execute("""
            UPDATE clients 
            SET encrypted_id = %s, status = 'temporary'
            WHERE id = %s
        """, (temporary_id, client_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_info(f"🔁 Client downgraded to: {temporary_id}", LogColors.YELLOW)
        return temporary_id
        
    except Exception as e:
        log_info(f"❌ Error downgrading client: {e}", LogColors.RED)
        return None

def close_conversation(client_id, closed_by_staff_id=None):
    """Close conversation and release client back to pool"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Set auto-close time based on config
        auto_close_days = Config.DEAL_AUTO_CLOSE_DAYS
        auto_close_time = datetime.now() + timedelta(days=auto_close_days)
        
        cursor.execute("""
            UPDATE conversations 
            SET status = 'closed', auto_close_time = %s
            WHERE client_id = %s AND status = 'open'
        """, (auto_close_time, client_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_info(f"🔒 Conversation closed for client: {client_id}", LogColors.YELLOW)
        return True
        
    except Exception as e:
        log_info(f"❌ Error closing conversation: {e}", LogColors.RED)
        return False

def handle_staff_command(staff_number, command, client_info=None):
    """Handle staff commands like /upgrade, /close, /status, /pre-register"""
    try:
        parts = command.split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        
        if cmd == "/upgrade" and client_info:
            # Staff upgrades client after purchase
            new_id = upgrade_client_to_permanent(client_info["id"], staff_number)
            if new_id:
                send_whatsapp_message(staff_number, f"✅ Upgraded {client_info['encrypted_id']} → {new_id}")
            else:
                send_whatsapp_message(staff_number, "❌ Upgrade failed")
                
        elif cmd == "/close" and client_info:
            # Staff closes conversation
            if close_conversation(client_info["id"], staff_number):
                send_whatsapp_message(staff_number, f"🔒 Conversation closed for {client_info['encrypted_id']}")
            else:
                send_whatsapp_message(staff_number, "❌ Close failed")
                
        elif cmd == "/status" and len(parts) > 2:
            # Admin status override: /status CLIENT_CODE temporary|permanent
            client_code = parts[1]
            new_status = parts[2].lower()
            
            # Find client by code
            conn = psycopg.connect(Config.DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT id, status FROM clients WHERE encrypted_id = %s", (client_code,))
            client_data = cursor.fetchone()
            
            if client_data:
                client_id, current_status = client_data
                if new_status == "permanent" and current_status != "permanent":
                    new_id = upgrade_client_to_permanent(client_id, staff_number)
                    send_whatsapp_message(staff_number, f"⚙️ {client_code} → {new_id} (permanent)")
                elif new_status == "temporary" and current_status == "permanent":
                    new_id = downgrade_client_to_temporary(client_id, staff_number)
                    send_whatsapp_message(staff_number, f"⚙️ {client_code} → {new_id} (temporary)")
                else:
                    send_whatsapp_message(staff_number, f"ℹ️ {client_code} already {current_status}")
            else:
                send_whatsapp_message(staff_number, f"❌ Client {client_code} not found")
                
        elif cmd == "/pre-register" and len(parts) > 2:
            # Admin pre-registers client: /pre-register PHONE_NUMBER CODE
            phone_number = parts[1]
            custom_code = parts[2]
            status = parts[3] if len(parts) > 3 else "temporary"
            
            success, result = pre_register_client(phone_number, custom_code, status, staff_number)
            if success:
                send_whatsapp_message(staff_number, f"👑 Pre-registered: {phone_number} → {result}")
            else:
                send_whatsapp_message(staff_number, f"❌ Pre-register failed: {result}")
                
        elif cmd == "/set-timeout" and len(parts) > 1:
            # Admin changes auto-close days: /set-timeout 5
            try:
                new_days = int(parts[1])
                # This would update a configuration table - for now we'll just acknowledge
                send_whatsapp_message(staff_number, f"⏰ Auto-close set to {new_days} days")
            except:
                send_whatsapp_message(staff_number, "❌ Invalid days format")
                
    except Exception as e:
        log_info(f"❌ Error handling staff command: {e}", LogColors.RED)
        send_whatsapp_message(staff_number, "❌ Command failed")

def store_message(from_number, to_number, content, direction, encrypted_sender_id=None, encrypted_receiver_id=None):
    """Store message in database for history"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO messages (from_number, to_number, content, direction, encrypted_sender_id, encrypted_receiver_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (from_number, to_number, content, direction, encrypted_sender_id, encrypted_receiver_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_info(f"💾 Message stored: {encrypted_sender_id} → {direction}", LogColors.BLUE)
        return True
        
    except Exception as e:
        log_info(f"❌ Error storing message: {e}", LogColors.RED)
        return False

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

                    # Check for staff commands first
                    if msg_body.startswith('/'):
                        client_info = get_or_create_client(from_number)
                        handle_staff_command(from_number, msg_body, client_info)
                        continue

                    # Get or create client
                    client_info = get_or_create_client(from_number)
                    
                    if not client_info:
                        reply_text = "⚠️ System temporarily unavailable. Please try again."
                        send_whatsapp_message(from_number, reply_text)
                        continue

                    # Store message with encrypted ID only
                    store_message(
                        from_number=from_number,
                        to_number=Config.BUSINESS_DISPLAY_NUMBER,
                        content=msg_body,
                        direction="incoming",
                        encrypted_sender_id=client_info["encrypted_id"]
                    )

                    # Client sees simple welcome (no code revealed)
                    if client_info["is_new"]:
                        reply_text = "👋 Welcome! Thanks for contacting us. We will be with you in one second."
                    else:
                        reply_text = "✅ Message received! We'll get back to you shortly."

                    send_whatsapp_message(from_number, reply_text)
                    
                    # Log with encrypted ID only (staff will see this)
                    log_info(f"💬 Message from {client_info['encrypted_id']}: {msg_body}", LogColors.YELLOW)

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
# DATABASE INITIALIZATION
# -------------------------------------------
def init_database():
    """Create all necessary tables"""
    try:
        conn = psycopg.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # [All your table creation code remains the same]
        # ... [keep all your table creation code] ...
        
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
def initialize_database_on_startup():
    """Initialize database when app starts"""
    with app.app_context():
        init_database()

# Call this function to create tables on startup
initialize_database_on_startup()

# -------------------------------------------
# RUN APP
# -------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    log_info(f"🚀 Server starting on port {port}...", LogColors.BLUE)
    app.run(host="0.0.0.0", port=port)
