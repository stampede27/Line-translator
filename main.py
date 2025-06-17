from flask import Flask, request
import requests
import os
import re
import json

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# Gemini 2.0 Flash API endpoint
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

@app.route("/")
def home():
    return "LINE Bot Webhook is running with Gemini 2.0"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    events = data.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]

            # Ignore if message is just emoji, sticker, or image
            if is_noise(user_text):
                continue

            # Process text and get reply
            response_text = process_message(user_text)
            if response_text:
                reply_message(reply_token, response_text)

        elif event["type"] == "unsend":
            message_id = event["unsend"]["messageId"]
            # Optional: You may implement a deletion tracking system if needed.

    return "OK"

def is_noise(text):
    # Ignore messages with only emojis, mentions, or abbreviations
    if all(ord(c) > 10000 or c in "@#" for c in text.strip()):
        return True
    return False

def clean_text(text):
    # Remove mentions and uppercase abbreviations from translation
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\b[A-Z]{2,}\b", "", text)
    return text.strip()

def detect_language(text):
    # Basic heuristic: count Han characters
    zh_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    en_count = len(re.findall(r"[a-zA-Z]", text))
    return "zh" if zh_count > en_count else "en"

def process_message(text):
    cleaned = clean_text(text)
    lang = detect_language(cleaned)

    if lang == "en":
        prompt = (
            f"You are a bilingual assistant. Rephrase this English sentence without changing its meaning, "
            f"and translate it into Traditional Chinese in slightly more formal way.\n\n"
            f"Sentence: {cleaned}"
        )
    else:
        prompt = (
            f"You are a bilingual assistant. Show the original Traditional Chinese sentence, "
            f"and translate it to English clearly.\n\n"
            f"Sentence: {cleaned}"
        )

    gemini_response = query_gemini(prompt)
    return gemini_response

def query_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, json=body)
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Error from Gemini:", response.json())
        return "⚠️ Sorry, something went wrong with Gemini."

def reply_message(token, message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
