from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Read environment variables (make sure to set these in Railway dashboard)
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

@app.route("/")
def home():
    return "LINE Bot Webhook is running!"

@app.route("/webhook", methods=['POST'])
def webhook():
    payload = request.json
    events = payload.get('events', [])

    for event in events:
        if event['type'] == 'message':
            user_text = event['message']['text']
            reply_token = event['replyToken']

            translated_text = ask_chatgpt("Translate to English: " + user_text)
            reply_message(reply_token, translated_text)

    return "OK"

def reply_message(token, message):
    headers = {
        "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": token,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

def ask_chatgpt(prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    return res.json()['choices'][0]['message']['content'].strip()

# This is needed to run on Railway (or any non-Replit host)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
