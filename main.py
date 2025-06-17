from flask import Flask, request
import requests
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

@app.route("/")
def home():
    return "LINE Bot with Gemini is running!"

@app.route("/webhook", methods=['POST'])
def webhook():
    payload = request.json
    events = payload.get('events', [])

    for event in events:
        if event['type'] == 'message':
            user_text = event['message']['text']
            reply_token = event['replyToken']

            if user_text.startswith("/ttw"):
                prompt = user_text[4:].strip()
                reply = handle_ttw(prompt)
            elif user_text.startswith("/ten"):
                prompt = user_text[4:].strip()
                reply = handle_ten(prompt)
            else:
                reply = "Please use /ttw or /ten command."

            reply_message(reply_token, reply)

    return "OK"

def handle_ttw(user_input):
    prompt = (
        f"Please rephrase the following sentence in correct English grammar "
        f"but do not change its meaning. Then translate it to Traditional Chinese. "
        f"First respond with the corrected English sentence, then below it write the Chinese translation.\n\n"
        f"Sentence: {user_input}"
    )
    return call_gemini_api(prompt)

def handle_ten(user_input):
    prompt = f"Translate the following Traditional Chinese sentence to English:\n{user_input}"
    return call_gemini_api(prompt)

def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return "⚠️ Unexpected Gemini response format."
    else:
        return f"⚠️ Error from Gemini: {response.json().get('error', {}).get('message', 'Unknown error')}"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
