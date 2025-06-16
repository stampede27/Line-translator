from flask import Flask, request
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']  # Set this in Railway or your environment

@app.route("/")
def home():
    return "LINE Translator Bot with Gemini is running!"

@app.route("/webhook", methods=['POST'])
def webhook():
    payload = request.json
    events = payload.get('events', [])

    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_text = event['message']['text']
            reply_token = event['replyToken']

            translated_text = ask_gemini("Translate to English: " + user_text)

            if translated_text:
                reply_message(reply_token, translated_text)
            else:
                reply_message(reply_token, "Sorry, I couldn’t understand that.")

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
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()

        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print("Error from Gemini:", e)
        return None
