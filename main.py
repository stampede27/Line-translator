from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables from Railway/GitHub
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

@app.route("/")
def home():
    return "LINE Gemini Translator Bot is running!"

@app.route("/webhook", methods=['POST'])
def webhook():
    payload = request.json
    events = payload.get('events', [])

    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_text = event['message']['text']
            reply_token = event['replyToken']

            translated_text = ask_gemini("Translate this to Traditional Chinese like a local Taiwanese:\n" + user_text)
            if not translated_text:
                translated_text = "Sorry, youdepunggol."

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

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print("Error from Gemini:", e)
        return None

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
