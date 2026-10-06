import os
import threading
import requests

from http.server import BaseHTTPRequestHandler, HTTPServer

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# =========================================================
# ENV
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
PLAYPAY_API_KEY = os.getenv("PLAYPAY_API_KEY", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "").strip()

PORT = int(os.getenv("PORT", "10000"))

API = "https://playpay.uz/api/v1"


# =========================================================
# CHECK
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if ":" not in BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN noto'g'ri")

if not PLAYPAY_API_KEY:
    raise RuntimeError("PLAYPAY_API_KEY missing")

if ADMIN_ID == 0:
    raise RuntimeError("ADMIN_ID missing")


# =========================================================
# BOT
# =========================================================

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}


# =========================================================
# PLAYPAY REQUEST
# =========================================================

def playpay(method, endpoint, data=None):

    headers = {
        "X-API-Key": PLAYPAY_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    url = API + endpoint

    try:

        if method == "GET":
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

        else:
            response = requests.post(
                url,
                headers=headers,
                json=data or {},
                timeout=30
            )

        try:
            return response.json()

        except Exception:
            return {
                "ok": False,
                "error": "API JSON javob qaytarmadi"
            }

    except Exception as e:

        print("PLAYPAY ERROR:", e)

        return {
            "ok": False,
            "error": "PlayPay bilan bog'lanib bo'lmadi"
        }


# =========================================================
# HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            b"YAKURA BOT ONLINE"
        )

    def log_message(self, format, *args):
        return


def start_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Health server running on port {PORT}"
    )

    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start_cmd(message):

    chat_id = message.chat.id

    user_states[chat_id] = {}

    games_response = playpay(
        "GET",
        "/games"
    )

    if not games_response.get("ok"):

        bot.send_message(
            chat_id,
            "❌ O'yinlar ro'yxatini yuklab bo'lmadi.\n\n"
            "Keyinroq qayta urinib ko'ring."
        )

        print(
            "GAMES ERROR:",
            games_response
        )

        return

    games = games_response.get(
        "games",
        []
    )

    # Boshlanishida faqat 4 ta o'yin
    # Keyin bu yerda qo'shimcha o'yinlarni ochamiz.

    allowed_names = [
        "PUBG Mobile",
        "Mobile Legends",
        "Free Fire",
        "Roblox",
    ]

    selected_games = []

    for game in games:

        name = game.get("name", "")

        if name in allowed_names:

            selected_games.append(game)

    # Agar PlayPay nomlari farq qilsa,
    # birinchi 4 ta faol o'yinni ko'rsatamiz.

    if not selected_games:

        selected_games = games[:4]

    markup = InlineKeyboardMarkup()

    for game in selected_games:

        game_id = game.get("game_id")
        name = game.get("name", "Game")

        markup.add(
            InlineKeyboardButton(
                f"🎮 {name}",
                callback_data=f"game_{game_id}"
            )
        )

    if ADMIN_USERNAME:

        markup.add(
            InlineKeyboardButton(
                "💬 Admin bilan bog'lanish",
                url=(
                    "https://t.me/"
                    + ADMIN_USERNAME.replace("@", "")
                )
            )
        )

    text = (
        "⚡️ YAKURA | DONAT STORE\n\n"
        "🎮 O'yinlar uchun tezkor donat.\n\n"
        "👇 O'yinni tanlang:"
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=markup
    )


# =========================================================
# CALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_handler(call):

    chat_id = call.message.chat.id

    try:
        bot.answer_callback_query(call.id)
    except:
        pass


    # =====================================================
    # GAME
    # =====================================================

    if call.data.startswith("game_"):

        game_id = call.data.replace(
            "game_",
            "",
            1
        )

        packages_response = playpay(
            "GET",
            f"/games/{game_id}/packages?currency=UZS"
        )

        if not packages_response.get("ok"):

            bot.send_message(
                chat_id,
                "❌ Paketlarni yuklab bo'lmadi."
            )

            return

        packages = packages_response.get(
            "packages",
            []
        )

        game_name = packages_response.get(
            "game",
            "O'yin"
        )

        if not packages:

            bot.send_message(
                chat_id,
                "❌ Bu o'yinda hozircha paket yo'q."
            )

            return

        user_states[chat_id] = {
            "game_id": int(game_id),
            "game_name": game_name,
            "packages": packages,
        }

        markup = InlineKeyboardMarkup()

        for package in packages:

            paket_id = package.get(
                "paket_id"
            )

            name = package.get(
                "name",
                "Paket"
            )

            price = package.get(
                "price",
                {}
            ).get(
                "amount",
                0
            )

            markup.add(
                InlineKeyboardButton(
                    f"📦 {name} — {price:,} so'm",
                    callback_data=f"package_{paket_id}"
                )
            )

        markup.add(
            InlineKeyboardButton(
                "⬅️ Orqaga",
                callback_data="back"
            )
        )

        bot.edit_message_text(
            f"🎮 {game_name}\n\n"
            "📦 Paketni tanlang:",
            chat_id,
            call.message.message_id,
            reply_markup=markup
        )

        return


    # =====================================================
    # PACKAGE
    # =====================================================

    if call.data.startswith("package_"):

        paket_id = call.data.replace(
            "package_",
            "",
            1
        )

        state = user_states.get(
            chat_id,
            {}
        )

        packages = state.get(
            "packages",
            []
        )

        selected = None

        for package in packages:

            if str(
                package.get("paket_id")
            ) == str(paket_id):

                selected = package
                break

        if not selected:

            bot.send_message(
                chat_id,
                "❌ Paket topilmadi."
            )

            return

        user_states[chat_id][
            "paket_id"
        ] = int(paket_id)

        user_states[chat_id][
            "package_name"
        ] = selected.get(
            "name",
            "Paket"
        )

        user_states[chat_id][
            "price"
        ] = selected.get(
            "price",
            {}
        ).get(
            "amount",
            0
        )

        user_states[chat_id][
            "step"
        ] = "wait_player_id"

        game_id = state.get(
            "game_id"
        )

        # O'yin haqida ma'lumotni yana olamiz
        games_response = playpay(
            "GET",
            "/games"
        )

        requires_server = False
        requires_charname = False
        id_label = "Player ID"

        for game in games_response.get(
            "games",
            []
        ):

            if str(
                game.get("game_id")
            ) == str(game_id):

                requires_server = game.get(
                    "requires_server",
                    False
                )

                requires_charname = game.get(
                    "requires_charname",
                    False
                )

                id_label = game.get(
                    "id_label",
                    "Player ID"
                )

                break

        user_states[chat_id][
            "requires_server"
        ] = requires_server

        user_states[chat_id][
            "requires_charname"
        ] = requires_charname

        user_states[chat_id][
            "id_label"
        ] = id_label

        bot.send_message(
            chat_id,
            f"✅ {selected.get('name')}\n"
            f"💰 {user_states[chat_id]['price']:,} so'm\n\n"
            f"🆔 {id_label} yuboring:"
        )

        return


    # =====================================================
    # BACK
    # =====================================================

    if call.data == "back":

        start_cmd(call.message)

        return


# =========================================================
# USER TEXT
# =========================================================

@bot.message_handler(
    content_types=["text", "photo"]
)
def handle_messages(message):

    chat_id = message.chat.id

    state = user_states.get(
        chat_id,
        {}
    )

    step = state.get(
        "step"
    )


    # =====================================================
    # PLAYER ID
    # =====================================================

    if step == "wait_player_id":

        if not message.text:

            bot.send_message(
                chat_id,
                "⚠️ ID raqamini matn ko'rinishida yuboring."
            )

            return

        player_id = message.text.strip()

        user_states[chat_id][
            "player_id"
        ] = player_id

        if state.get(
            "requires_server"
        ):

            user_states[chat_id][
                "step"
            ] = "wait_server"

            bot.send_message(
                chat_id,
                "🌐 Server / Zone ID yuboring:"
            )

            return

        validate_player(
            chat_id
        )

        return


    # =====================================================
    # SERVER
    # =====================================================

    if step == "wait_server":

        server_id = message.text.strip()

        user_states[chat_id][
            "server_id"
        ] = server_id

        validate_player(
            chat_id
        )

        return


    # =====================================================
    # RECEIPT
    # =====================================================

    if step == "wait_receipt":

        if not message.photo:

            bot.send_message(
                chat_id,
                "⚠️ To'lov chekini rasm qilib yuboring."
            )

            return

        photo_id = message.photo[-1].file_id

        price = state.get(
            "price",
            0
        )

        username = (
            message.from_user.username
            or "Username yo'q"
        )

        admin_text = (
            "📥 YANGI BUYURTMA\n\n"
            f"👤 @{username}\n"
            f"🆔 Telegram ID: {chat_id}\n\n"
            f"🎮 O'yin: {state.get('game_name')}\n"
            f"📦 Paket: {state.get('package_name')}\n"
            f"💰 Narx: {price:,} so'm\n"
            f"🆔 Player ID: {state.get('player_id')}\n"
            f"🌐 Server: {state.get('server_id', '-')}\n"
            f"👤 Nickname: {state.get('player_name', '-')}\n"
        )

        bot.send_photo(
            ADMIN_ID,
            photo_id,
            caption=admin_text
        )

        bot.send_message(
            chat_id,
            "✅ Chek qabul qilindi!\n\n"
            "Admin to'lovni tekshiradi."
        )

        user_states[chat_id] = {}

        return


# =========================================================
# VALIDATE PLAYER
# =========================================================

def validate_player(chat_id):

    state = user_states.get(
        chat_id,
        {}
    )

    data = {
        "game_id": state.get(
            "game_id"
        ),
        "player_id": state.get(
            "player_id"
        ),
    }

    if state.get(
        "requires_server"
    ):

        data["server_id"] = state.get(
            "server_id"
        )

    if state.get(
        "requires_charname"
    ):

        data["charname"] = state.get(
            "charname"
        )

    result = playpay(
        "POST",
        "/check_id",
        data
    )

    print(
        "CHECK ID:",
        result
    )

    if not result.get("ok"):

        bot.send_message(
            chat_id,
            "❌ ID tekshirishda xatolik.\n\n"
            f"{result.get('error', 'Nomaʼlum xatolik')}"
        )

        return

    if not result.get("valid"):

        bot.send_message(
            chat_id,
            "❌ Bu ID topilmadi yoki noto'g'ri.\n\n"
            "ID/Serverni tekshirib qayta yuboring."
        )

        return

    player_name = result.get(
        "player_name",
        ""
    )

    user_states[chat_id][
        "player_name"
    ] = player_name

    user_states[chat_id][
        "step"
    ] = "wait_receipt"

    price = state.get(
        "price",
        0
    )

    payment = (
        "✅ AKKAUNT TOPILDI\n\n"
        f"👤 Nickname: {player_name}\n"
        f"🆔 ID: {state.get('player_id')}\n"
    )

    if state.get(
        "requires_server"
    ):

        payment += (
            f"🌐 Server: "
            f"{state.get('server_id')}\n"
        )

    payment += (
        "\n"
        f"📦 Paket: {state.get('package_name')}\n"
        f"💰 To'lov: {price:,} so'm\n\n"
        "💳 TO'LOV\n\n"
        f"Karta: {CARD_NUMBER}\n"
        f"Karta egasi: {CARD_HOLDER}\n\n"
        "To'lovni amalga oshiring va "
        "chek rasmini shu yerga yuboring."
    )

    bot.send_message(
        chat_id,
        payment
    )


# =========================================================
# RUN
# =========================================================

print("YAKURA BOT started")

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
        )
