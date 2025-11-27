from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import os
import uuid
from youtubesearchpython import VideosSearch

# ---------------- Bot token ----------------
BOT_TOKEN = "8423512518:AAGbtdHtEdyOVjFvuONq5S1W9ZKuqeBNloU"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

VIDEO_TEXT = "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @KeepingInsta_Bot"

# ---------------- Commands ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "Assalomu Alaykum 👋!\n\n"
        "YouTubedan yoki Instagramdan video linkini yuboring yoki musiqa nomini yozing.\n\n"
        "Tugmalar yordamida video va musiqani yuklab olishingiz mumkin.\n\n"
    )

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(
        msg.chat.id,
        "Bot ishlatish:\n"
        "1️⃣ YouTubedan yoki Instagramdan video linkini yuboring\n"
        "2️⃣ Video pastidagi 🎵 tugmasi orqali Musiqani yulab oling oling\n"
        "3️⃣ Faqat musiqa nomini yozsangiz, bot topib Musiqani chiqarib beradi"
        "/start - Botni ishga tushirish\n"
        "/help - Qo'llanma\n"
        "/about - Bot haqida\n\n"
        "Botda biror muammo bo'lsa: @Enective ga murojaat qiling."
    )

@bot.message_handler(commands=['about'])
def about(msg):
    bot.send_message(
        msg.chat.id,
        "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @KeepingInsta_Bot\n"
        "Telegram Kanalimiz: @aclubnc\n"
        "Username: @KeepingInsta_Bot"
        "Dasturchi: @thexamidovs > Nabiyulloh.X 🧑‍💻"
    )

# ---------------- Message handler ----------------
@bot.message_handler(func=lambda m: True)
def handle_msg(msg):
    text = msg.text.strip()
    if text.startswith("https://") or text.startswith("http://"):
        try:
            file_path = download_video(text)
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🎵 Qo‘shiqni yuklab olish", callback_data=f"get_audio|{text}")
            )
            bot.send_video(msg.chat.id, open(file_path, 'rb'), caption=VIDEO_TEXT, reply_markup=markup)
            os.remove(file_path)
        except Exception as e:
            bot.send_message(msg.chat.id, f"Xatolik: {str(e)}")
    else:
        try:
            url, title = search_youtube(text)
            file_path = download_audio(url)
            bot.send_audio(msg.chat.id, open(file_path, 'rb'), title=title)
            os.remove(file_path)
        except Exception as e:
            bot.send_message(msg.chat.id, f"Musiqa topilmadi yoki xatolik: {str(e)}")

# ---------------- Callback handler ----------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("get_audio|"):
        url = call.data.split("|")[1]
        try:
            file_path = download_audio(url)
            bot.send_audio(call.message.chat.id, open(file_path, 'rb'))
            os.remove(file_path)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Audio yuklab bo‘lmadi: {str(e)}")

# ---------------- Helper functions ----------------
def download_video(url):
    out_file = f"{uuid.uuid4()}.mp4"
    ydl_opts = {'outtmpl': out_file, 'format': 'bestvideo+bestaudio'}
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_file

def download_audio(url):
    out_file = f"{uuid.uuid4()}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_file,
        'postprocessors': [
            {'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}
        ]
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_file

def search_youtube(query):
    result = VideosSearch(query, limit=1).result()
    if result['result']:
        video = result['result'][0]
        return video['link'], video['title']
    else:
        raise Exception("Video topilmadi ❌")

# ---------------- Flask webhook for Render ----------------
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route("/")
def index():
    return "Bot ishlayapti ✅"

# ---------------- Start bot ----------------
if __name__ == "__main__":
    bot.remove_webhook()
    # Render.com uchun URL o'zgartiriladi
    bot.set_webhook(url=f"https://keepinginstabot.onrender.com/{BOT_TOKEN}")
    # Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
