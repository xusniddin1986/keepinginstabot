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

# Callback uchun vaqtinchalik dictionary
callback_dict = {}

# TEMP PAPKA (Render serverda)
TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ---------------- Commands ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "Assalomu Alaykum 👋!\n\n"
        "YouTubedan yoki Instagramdan video linkini yuboring yoki musiqa nomini yozing.\n\n"
        "Tugmalar yordamida video va musiqani yuklab olishingiz mumkin.\n\n"
        "Qo'llanma bilan tanishib chiqing: /help\n"
    )

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(
        msg.chat.id,
        "Bot ishlatish:\n"
        "1️⃣ YouTube/Instagram video link yuboring\n"
        "2️⃣ 🎵 tugmasi orqali Musiqani yuklab oling\n"
        "3️⃣ Musiqa nomini yozsangiz — bot o‘zi topadi\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Qo'llanma\n"
        "/about - Bot haqida\n"
        "Muammo bo'lsa → @Enective"
    )

@bot.message_handler(commands=['about'])
def about(msg):
    bot.send_message(
        msg.chat.id,
        "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @KeepingInsta_Bot\n"
        "Kanal: @aclubnc\n"
        "Dasturchi: @thexamidovs (Nabiyulloh.X)"
        "Bot Admini: @Enective"
    )

# ---------------- Message handler ----------------
@bot.message_handler(func=lambda m: True)
def handle_msg(msg):
    text = msg.text.strip()

    # ------- LINK bo‘lsa →
    if text.startswith("https://") or text.startswith("http://"):
        try:
            loading_msg = bot.send_message(msg.chat.id, "⏳ Video yuklanmoqda...")

            file_path = download_video(text)

            uid = str(uuid.uuid4())
            callback_dict[uid] = text

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🎵 Qo‘shiqni yuklab olish", callback_data=f"get_audio|{uid}")
            )

            bot.send_video(
                msg.chat.id,
                open(file_path, 'rb'),
                caption=VIDEO_TEXT,
                reply_markup=markup
            )

            #  Video chiqarilgandan keyin "yuklanmoqda" ni o‘chirish
            bot.delete_message(msg.chat.id, loading_msg.message_id)

            os.remove(file_path)

        except Exception as e:
            bot.send_message(msg.chat.id, f"Xatolik: {str(e)}")

    else:
        # ------- MUSIC SEARCH (YouTube search)
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
        uid = call.data.split("|")[1]
        url = callback_dict.get(uid)

        if not url:
            bot.send_message(call.message.chat.id, "Audio yuklab bo‘lmadi: URL topilmadi ❌")
            return

        try:
            bot.send_message(call.message.chat.id, "🎧 Audio tayyorlanmoqda...")

            file_path = download_audio(url)
            bot.send_audio(call.message.chat.id, open(file_path, 'rb'))

            os.remove(file_path)

        except Exception as e:
            bot.send_message(call.message.chat.id, f"Audio yuklab bo‘lmadi: {str(e)}")


# ---------------- Helper functions ----------------
def download_video(url):
    out_file = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp4")

    ydl_opts = {
        'outtmpl': out_file,
        'format': 'best[ext=mp4]/best'
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return out_file


def download_audio(url):
    out_file = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_file,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }
        ]
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return out_file


def search_youtube(query):
    result = VideosSearch(query, limit=1).result()

    if result["result"]:
        video = result["result"][0]
        return video["link"], video["title"]

    raise Exception("Topilmadi ❌")


# ---------------- Webhook (Render) ----------------
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

@app.route("/")
def home():
    return "Bot ishlayapti 🚀"


# ---------------- Start bot ----------------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://keepinginstabot.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
