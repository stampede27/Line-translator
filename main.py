from flask import Flask, request
import requests
import google.generativeai as genai
import os

app = Flask(__name__)

# Environment variables
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

@app.route('/')
def home():
    return "Gemini-powered LINE Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    events = payload.get('events', [])

    for event in events:
        if event['type'] == 'message' and 'text' in event['message']:
            user_text = event['message']['text']
            reply_token = event['replyToken']
            
            if user_text.lower().startswith('/ttw'):
                content = user_text[4:].strip()
                english, chinese = process_ttw(content)
                reply = f"{english}\n\n{chinese}"

            elif user_text.lower().startswith('/ten'):
                content = user_text[4:].strip()
                english = translate_chinese_to_english(content)
                reply = english

            else:
                reply = "指令錯誤。請使用 /ttw 或 /ten."

            reply_message(reply_token, reply)

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

def process_ttw(text):
    try:
        prompt = (
            f"Please help rephrase this English sentence to make it grammatically correct, "
            f"but do not change the meaning:\n{text}\n"
            f"Then translate the rephrased version into Traditional Chinese. "
            f"Reply in this format:\n\nEnglish: <corrected>\nChinese: <translated>"
        )
        response = model.generate_content(prompt)
        result = response.text

        if "English:" in result and "Chinese:" in result:
            english = result.split("English:")[1].split("Chinese:")[0].strip()
            chinese = result.split("Chinese:")[1].strip()
        else:
            english = "Sorry, something went wrong."
            chinese = ""

        return english, chinese
    except Exception as e:
        print("Error:", e)
        return "Sorry, I couldn't process that.", ""

def translate_chinese_to_english(text):
    try:
        prompt = f"Please translate the following Traditional Chinese text to natural English:\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Error:", e)
        return "Sorry, I couldn't translate that."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
