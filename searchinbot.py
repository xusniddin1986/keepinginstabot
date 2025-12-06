from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import os
import uuid
import json

# ---------------- Bot token ----------------
BOT_TOKEN = "8423512518:AAGbtdHtEdyOVjFvuONq5S1W9ZKuqeBNloU"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

VIDEO_TEXT = "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @KeepingInsta_Bot"
ADMIN_ID = 5714265632
ADMIN_FILE = "admins.json"
WELCOME_TEXT_FILE = "welcome.json"

TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ---------------- Admin data ----------------
def load_admins():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as f:
            return json.load(f)
    else:
        admins = [ADMIN_ID]
        with open(ADMIN_FILE, "w") as f:
            json.dump(admins, f)
        return admins

def save_admins(admins):
    with open(ADMIN_FILE, "w") as f:
        json.dump(admins, f)

admins = load_admins()

# ---------------- Welcome text ----------------
def load_welcome():
    if os.path.exists(WELCOME_TEXT_FILE):
        with open(WELCOME_TEXT_FILE, "r") as f:
            return json.load(f).get("text", "Assalomu Alaykum!")
    return "Assalomu Alaykum!"

def save_welcome(text):
    with open(WELCOME_TEXT_FILE, "w") as f:
        json.dump({"text": text}, f)

welcome_text = load_welcome()

# ---------------- Callback dict ----------------
callback_dict = {}

# ---------------- Commands ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.chat.id,
        f"{welcome_text}\n\nYouTubedan, TikTok yoki Instagramdan video linkini yuboring yoki musiqa nomini yozing.\n\nTugmalar yordamida video va musiqani yuklab olishingiz mumkin.\n\nQo'llanma bilan tanishib chiqing: /help"
    )

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(
        msg.chat.id,
        "Bot ishlatish:\n"
        "1️⃣ YouTube/TikTok/Instagram video link yuboring\n"
        "2️⃣ 🎵 tugmasi orqali Musiqani yuklab oling\n"
        "3️⃣ Musiqa nomini yozsangiz — bot 10 ta variant chiqaradi\n\n"
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
        "Dasturchi: @thexamidovs (Nabiyulloh.X)\n"
        "Bot Admini: @Enective"
    )

# ---------------- Admin Panel ----------------
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id not in admins:
        bot.send_message(msg.chat.id, "Sizda ruxsat yo‘q ❌")
        return

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        InlineKeyboardButton("👤 Admin qo‘shish", callback_data="admin_add"),
        InlineKeyboardButton("❌ Admin o‘chirish", callback_data="admin_remove"),
        InlineKeyboardButton("📝 Welcome matnini o‘zgartirish", callback_data="admin_setwelcome"),
        InlineKeyboardButton("📜 Adminlar ro‘yxati", callback_data="admin_list")
    )

    bot.send_message(msg.chat.id, "Admin panel:", reply_markup=markup)

# ---------------- Message handler ----------------
@bot.message_handler(func=lambda m: True)
def handle_msg(msg):
    text = msg.text.strip()

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

            bot.delete_message(msg.chat.id, loading_msg.message_id)
            os.remove(file_path)

        except Exception as e:
            bot.send_message(msg.chat.id, f"Xatolik: {str(e)}")
    else:
        try:
            results = search_youtube(text, limit=10)
            if not results:
                raise Exception("Hech narsa topilmadi ❌")

            markup = InlineKeyboardMarkup()
            for idx, video in enumerate(results, start=1):
                markup.add(
                    InlineKeyboardButton(f"{idx}. {video['title']}", callback_data=f"select_music|{video['link']}")
                )

            bot.send_message(msg.chat.id, "Topilgan qo‘shiqlar:", reply_markup=markup)

        except Exception as e:
            bot.send_message(msg.chat.id, f"Musiqa topilmadi yoki xatolik: {str(e)}")

# ---------------- Callback handler ----------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data

    if data.startswith("get_audio|"):
        uid = data.split("|")[1]
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

    elif data.startswith("select_music|"):
        url = data.split("|")[1]
        try:
            file_path = download_audio(url)
            bot.send_audio(call.message.chat.id, open(file_path, 'rb'))
            os.remove(file_path)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Audio yuklab bo‘lmadi: {str(e)}")

    elif call.from_user.id not in admins:
        bot.answer_callback_query(call.id, "Sizda ruxsat yo‘q ❌")
        return

    elif data == "admin_stats":
        bot.send_message(call.message.chat.id, f"Admin statistikasi:\nFoydalanuvchilar soni: ---\nYuklashlar soni: ---")
    elif data == "admin_list":
        bot.send_message(call.message.chat.id, f"Hozirgi adminlar: {admins}")
    elif data == "admin_add":
        bot.send_message(call.message.chat.id, "Foydalanuvchi ID kiriting:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, add_admin)
    elif data == "admin_remove":
        bot.send_message(call.message.chat.id, "Foydalanuvchi ID kiriting:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, remove_admin)
    elif data == "admin_setwelcome":
        bot.send_message(call.message.chat.id, "Yangi welcome matnini yozing:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, set_welcome)

# ---------------- Admin helper functions ----------------
def add_admin(msg):
    try:
        new_id = int(msg.text.strip())
        if new_id not in admins:
            admins.append(new_id)
            save_admins(admins)
            bot.send_message(msg.chat.id, f"{new_id} adminlarga qo‘shildi ✅")
        else:
            bot.send_message(msg.chat.id, "Bu foydalanuvchi allaqachon admin ✅")
    except:
        bot.send_message(msg.chat.id, "Noto‘g‘ri ID ❌")

def remove_admin(msg):
    try:
        rem_id = int(msg.text.strip())
        if rem_id in admins:
            admins.remove(rem_id)
            save_admins(admins)
            bot.send_message(msg.chat.id, f"{rem_id} adminlardan o‘chirildi ❌")
        else:
            bot.send_message(msg.chat.id, "Bu foydalanuvchi admin emas ❌")
    except:
        bot.send_message(msg.chat.id, "Noto‘g‘ri ID ❌")

def set_welcome(msg):
    global welcome_text
    welcome_text = msg.text.strip()
    save_welcome(welcome_text)
    bot.send_message(msg.chat.id, f"Welcome matni o‘zgartirildi ✅\nYangi matn: {welcome_text}")

# ---------------- Helper functions ----------------
def download_video(url):
    out_file = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp4")
    ydl_opts = {
        'outtmpl': out_file,
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True
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
            {'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}
        ],
        'noplaylist': True,
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_file

def search_youtube(query, limit=10):
    search = VideosSearch(query, limit=limit)
    videos = []
    result = search.result()
    if "result" in result and result["result"]:
        for video in result["result"]:
            videos.append({"title": video["title"], "link": video["link"]})
    return videos

# ---------------- Webhook ----------------
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

@app.route("/")
def home():
    return "Bot ishlayapti 🚀"

# ---------------- Run bot ----------------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://keepinginstabot.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))