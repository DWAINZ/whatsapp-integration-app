from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

ACCESS_TOKEN = "EAAUhVZCAVsWABPqvZB1NuewJUOQJgHWdtee067bkzVe6DKXcZBoldlY8UxJ07e8RP09U6UYKcsnCvtu2ix7z7hFAafxqAw2zXcooqKWKVRD5fqjCmwtDpmUSUvUqyZBhixBpFnthreV6V6rGZAQuDMeYjEP04iedbkffZCkR5n4sJGFDX8wNTBp9RL8Iif9rZBTAgM0EcGaJDlN9b5ZAiuPLnhLNU1PDHyF1OQsAyba6dXknMbqGJswVYQDlFgZDZD"  # Replace with your actual WhatsApp API access token
PHONE_NUMBER_ID = "839043219287688"  # Replace with your actual phone number ID
API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

@app.route('/')
def home():
    return "✅ WhatsApp Integration App is running!"

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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
