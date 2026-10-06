import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
G2BULK_API_KEY = os.getenv("G2BULK_API_KEY", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "").strip()

PORT = int(os.getenv("PORT", "10000"))


# =========================================================
# TEKSHIRUV
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if ":" not in BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN noto'g'ri")

if not G2BULK_API_KEY:
    raise RuntimeError("G2BULK_API_KEY missing")

if ADMIN_ID == 0:
    raise RuntimeError("ADMIN_ID missing")


# =========================================================
# BOT
# =========================================================

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"YAKURA BOT ONLINE")

    def log_message(self, format, *args):
        return


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Health server running on port {PORT}")
    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================================================
# O'YINLAR
# =========================================================

GAMES = {

    "pubg": {
        "title": "📱 PUBG Mobile",
        "items": [
            {"id": "p1", "name": "60 UC", "price": 14000},
            {"id": "p2", "name": "325 UC", "price": 68000},
            {"id": "p3", "name": "660 UC", "price": 135000},
            {"id": "p4", "name": "1800 UC", "price": 360000},
        ]
    },

    "freefire": {
        "title": "🔥 Free Fire",
        "items": [
            {"id": "f1", "name": "100 + 10 Diamonds", "price": 15000},
            {"id": "f2", "name": "530 + 53 Diamonds", "price": 65000},
            {"id": "f3", "name": "1080 + 108 Diamonds", "price": 130000},
        ]
    },

    "mobile_legends": {
        "title": "⚔️ Mobile Legends",
        "items": [
            {"id": "m1", "name": "86 Diamonds", "price": 20000},
            {"id": "m2", "name": "172 Diamonds", "price": 40000},
            {"id": "m3", "name": "257 Diamonds", "price": 60000},
        ]
    },

    "roblox": {
        "title": "🧱 Roblox",
        "items": [
            {"id": "r1", "name": "80 Robux", "price": 18000},
            {"id": "r2", "name": "400 Robux", "price": 75000},
            {"id": "r3", "name": "800 Robux", "price": 145000},
        ]
    },

    "brawl_stars": {
        "title": "⭐ Brawl Stars",
        "items": [
            {"id": "b1", "name": "30 Gems", "price": 25000},
            {"id": "b2", "name": "80 Gems", "price": 60000},
            {"id": "b3", "name": "170 Gems", "price": 125000},
        ]
    },

    "custom": {
        "title": "➕ Boshqa o'yin yoki ilova",
        "items": []
    }
}


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start_cmd(message):

    user_states[message.chat.id] = {}

    markup = InlineKeyboardMarkup()

    for key, game in GAMES.items():

        markup.add(
            InlineKeyboardButton(
                game["title"],
                callback_data=f"game_{key}"
            )
        )

    if ADMIN_USERNAME:

        markup.add(
            InlineKeyboardButton(
                "💬 Admin bilan bog'lanish",
                url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
            )
        )

    text = (
        "⚡️ YAKURA | DONAT STORE\n\n"
        "🎮 O'yin va ilovalar uchun donat xizmati.\n\n"
        "👇 Kerakli o'yinni tanlang:"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


# =========================================================
# CALLBACK
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    chat_id = call.message.chat.id

    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    # O'YIN

    if call.data.startswith("game_"):

        game_key = call.data.replace("game_", "", 1)

        if game_key == "custom":

            user_states[chat_id] = {
                "game": "Boshqa o'yin/ilova",
                "step": "wait_custom"
            }

            bot.send_message(
                chat_id,
                "✍️ O'yin yoki ilova nomini yozing.\n\n"
                "Masalan:\n"
                "FC Mobile\n"
                "Telegram Premium\n"
                "Discord Nitro"
            )

            return

        game = GAMES.get(game_key)

        if not game:
            return

        user_states[chat_id] = {
            "game": game["title"]
        }

        markup = InlineKeyboardMarkup()

        for item in game["items"]:

            markup.add(
                InlineKeyboardButton(
                    f"{item['name']} — {item['price']:,} so'm",
                    callback_data=f"item_{item['id']}"
                )
            )

        markup.add(
            InlineKeyboardButton(
                "⬅️ Orqaga",
                callback_data="back"
            )
        )

        bot.edit_message_text(
            f"🎮 {game['title']}\n\n"
            "📦 Paketni tanlang:",
            chat_id,
            call.message.message_id,
            reply_markup=markup
        )

        return

    # ITEM

    if call.data.startswith("item_"):

        item_id = call.data.replace("item_", "", 1)

        selected = None

        for game in GAMES.values():

            for item in game["items"]:

                if item["id"] == item_id:
                    selected = item
                    break

            if selected:
                break

        if not selected:
            return

        user_states.setdefault(chat_id, {})

        user_states[chat_id]["item_name"] = selected["name"]
        user_states[chat_id]["price"] = selected["price"]
        user_states[chat_id]["step"] = "wait_game_id"

        bot.send_message(
            chat_id,
            f"✅ Paket: {selected['name']}\n"
            f"💰 Narx: {selected['price']:,} so'm\n\n"
            "🆔 Endi o'yin ID raqamingizni yuboring:"
        )

        return

    # BACK

    if call.data == "back":

        start_cmd(call.message)


# =========================================================
# USER MESSAGES
# =========================================================

@bot.message_handler(content_types=["text", "photo"])
def handle_messages(message):

    chat_id = message.chat.id

    state = user_states.get(chat_id, {})

    step = state.get("step")


    # CUSTOM GAME

    if step == "wait_custom":

        user_states[chat_id]["item_name"] = message.text
        user_states[chat_id]["price"] = "Kelishiladi"
        user_states[chat_id]["step"] = "wait_game_id"

        bot.send_message(
            chat_id,
            "🆔 Endi o'yin/ilova ID yoki kerakli ma'lumotni yuboring:"
        )

        return


    # GAME ID

    if step == "wait_game_id":

        user_states[chat_id]["account_info"] = message.text
        user_states[chat_id]["step"] = "wait_receipt"

        price = state.get("price")

        if isinstance(price, int):
            price_text = f"{price:,} so'm"
        else:
            price_text = str(price)

        payment = (
            "💳 TO'LOV\n\n"
            f"Karta: {CARD_NUMBER}\n"
            f"Karta egasi: {CARD_HOLDER}\n\n"
            f"💰 Summa: {price_text}\n\n"
            "To'lovni amalga oshirgach, "
            "chek rasmini shu yerga yuboring."
        )

        bot.send_message(
            chat_id,
            payment
        )

        return


    # RECEIPT

    if step == "wait_receipt" and message.photo:

        photo_id = message.photo[-1].file_id

        price = state.get("price")

        if isinstance(price, int):
            price_text = f"{price:,} so'm"
        else:
            price_text = str(price)

        username = message.from_user.username or "Username yo'q"

        admin_text = (
            "📥 YANGI BUYURTMA\n\n"
            f"👤 @{username}\n"
            f"🆔 Telegram ID: {chat_id}\n\n"
            f"🎮 O'yin: {state.get('game')}\n"
            f"📦 Paket: {state.get('item_name')}\n"
            f"💰 Narx: {price_text}\n"
            f"🆔 Account ID: {state.get('account_info')}"
        )

        bot.send_photo(
            ADMIN_ID,
            photo_id,
            caption=admin_text
        )

        bot.send_message(
            chat_id,
            "✅ Buyurtmangiz qabul qilindi!\n\n"
            "Admin to'lovni tekshiradi va buyurtmani qayta ishlaydi."
        )

        user_states[chat_id] = {}

        return


    if step == "wait_receipt":

        bot.send_message(
            chat_id,
            "⚠️ Iltimos, to'lov chekini rasm ko'rinishida yuboring."
        )


# =========================================================
# START BOT
# =========================================================

print("YAKURA G2Bulk started")

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
        )
