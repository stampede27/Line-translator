from flask import Flask, request
import requests
import os
import re
import json
from collections import defaultdict
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# In-memory store of messageId to userId (or reply tokens) and timestamp
message_map = defaultdict(dict)

@app.route("/")
def home():
    return "LINE Bot Webhook is running with Gemini 2.0 Flash"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    events = data.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_id = event["source"].get("userId")
            message_id = event["message"]["id"]
            text = event["message"]["text"]
            reply_token = event["replyToken"]

            if is_noise(text):
                continue

            response_text = process_message(text)
            if response_text:
                # Reply and store reference
                reply_message(reply_token, response_text)
                message_map[message_id] = {
                    "userId": user_id,
                    "timestamp": int(time.time())
                }

        elif event["type"] == "unsend":
            unsent_id = event["unsend"]["messageId"]
            if unsent_id in message_map:
                user_id = message_map[unsent_id]["userId"]
                push_unsend_notice(user_id)
                del message_map[unsent_id]

    return "OK"

def is_noise(text):
    if not text.strip():
        return True
    if re.fullmatch(r'[\U00010000-\U0010ffff\s]+', text):
        return True
    return False

def clean_text(text):
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\b[A-Z]{2,}\b", "", text)
    return text.strip()

def detect_language(text):
    zh_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    en_count = len(re.findall(r"[a-zA-Z]", text))
    return "zh" if zh_count > en_count else "en"

def process_message(text):
    cleaned = clean_text(text)
    lang = detect_language(cleaned)

    if lang == "en":
        prompt = (
            "You are a bilingual assistant. Rephrase the following English sentence "
            "without changing its meaning, then translate it to Traditional Chinese. "
            "Do not add any explanation or suggestions. Only output the following format:\n\n"
            "Rephrase sentence:\n{rephrased sentence}\n\nTranslation in Chinese:\n{chinese sentence}\n\n"
            f"Sentence: {cleaned}"
        )
    else:
        prompt = (
            "你是一個雙語助理。首先顯示使用者輸入的原始中文句子，然後將它清楚翻譯為英文。"
            "不要加入任何說明或建議。只輸出以下格式：\n\n"
            "原始中文：\n{original sentence}\n\n英文翻譯：\n{english translation}\n\n"
            f"句子：{cleaned}"
        )

    return query_gemini(prompt)

def query_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, json=body)

    try:
        result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return result
    except Exception as e:
        print("Gemini error:", response.text)
        return "⚠️ Gemini 無法處理這個訊息。"

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

def push_unsend_notice(user_id):
    """Simulate deletion message by pushing a ghost message"""
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": "（使用者已刪除訊息，翻譯已自動移除）"
        }]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
