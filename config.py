from flask import Flask, request, jsonify
import requests
import os
import datetime
import sys
import pytz
import psycopg2
from config import Config

app = Flask(__name__)

# ... [your existing configuration and utilities] ...

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
# DATABASE TEST ROUTE
# -------------------------------------------
@app.route("/test-db", methods=["GET"])
def test_database():
    """Test database connection"""
    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
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

# ... [your existing webhook routes] ...
