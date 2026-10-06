import os
import html
import uuid
import logging
import requests
import telebot

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
G2BULK_API_KEY = os.getenv("G2BULK_API_KEY")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").replace("@", "")

CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_HOLDER = os.getenv("CARD_HOLDER", "")

G2BULK_URL = "https://api.g2bulk.com/v1"

# YAKURA ustamasi
MARKUP_PERCENT = float(os.getenv("MARKUP_PERCENT", "10"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

if not G2BULK_API_KEY:
    raise RuntimeError("G2BULK_API_KEY missing")

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

# user_id -> state
users = {}


# =========================
# G2BULK
# =========================

class G2Bulk:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": G2BULK_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def get_games(self):
        r = self.session.get(
            f"{G2BULK_URL}/games",
            timeout=20
        )
        r.raise_for_status()
        return r.json()

    def get_fields(self, game_code):
        r = self.session.post(
            f"{G2BULK_URL}/games/fields",
            json={"game_code": game_code},
            timeout=20
        )
        r.raise_for_status()
        return r.json()

    def get_servers(self, game_code):
        r = self.session.post(
            f"{G2BULK_URL}/games/servers",
            json={"game_code": game_code},
            timeout=20
        )

        if r.status_code == 403:
            return {}

        r.raise_for_status()
        return r.json()

    def catalogue(self, game_code):
        r = self.session.get(
            f"{G2BULK_URL}/games/{game_code}/catalogue",
            timeout=20
        )
        r.raise_for_status()
        return r.json()

    def check_player(self, game_code, player_id, server_id=None):

        data = {
            "game_code": game_code,
            "player_id": player_id
        }

        if server_id:
            data["server_id"] = server_id

        r = self.session.post(
            f"{G2BULK_URL}/games/checkPlayerId",
            json=data,
            timeout=20
        )

        r.raise_for_status()
        return r.json()

    def order(
        self,
        game_code,
        catalogue_name,
        player_id,
        server_id=None
    ):

        data = {
            "catalogue_name": catalogue_name,
            "player_id": player_id,
            "remark": "YAKURA"
        }

        if server_id:
            data["server_id"] = server_id

        headers = {
            "X-Idempotency-Key": str(uuid.uuid4())
        }

        r = self.session.post(
            f"{G2BULK_URL}/games/{game_code}/order",
            json=data,
            headers=headers,
            timeout=30
        )

        r.raise_for_status()
        return r.json()

    def order_status(self, order_id, game_code):

        r = self.session.post(
            f"{G2BULK_URL}/games/order/status",
            json={
                "order_id": order_id,
                "game_code": game_code
            },
            timeout=20
        )

        r.raise_for_status()
        return r.json()


g2bulk = G2Bulk()


# =========================
# HELPERS
# =========================

def money(value):
    try:
        return f"{float(value):,.0f} so'm"
    except:
        return str(value)


def markup_price(price):
    return round(
        float(price) * (1 + MARKUP_PERCENT / 100),
        2
    )


def get_list(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in [
            "data",
            "games",
            "items",
            "results",
            "catalogue",
            "products"
        ]:
            if isinstance(data.get(key), list):
                return data[key]

    return []


def game_code(game):
    return str(
        game.get("code")
        or game.get("game_code")
        or game.get("slug")
        or ""
    )


def game_name(game):
    return str(
        game.get("name")
        or game.get("title")
        or game.get("game_name")
        or game_code(game)
    )


def product_name(product):
    return str(
        product.get("name")
        or product.get("title")
        or product.get("product_name")
        or product.get("catalogue_name")
        or "Paket"
    )


def product_price(product):
    for key in [
        "price",
        "amount",
        "selling_price",
        "cost",
        "normal_price"
    ]:
        if product.get(key) is not None:
            try:
                return float(product[key])
            except:
                pass

    return 0


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    users[message.chat.id] = {}

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "🎮 O'yinlar",
            callback_data="games"
        )
    )

    if ADMIN_USERNAME:
        kb.add(
            InlineKeyboardButton(
                "👤 Admin",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        )

    bot.send_message(
        message.chat.id,
        "⚡ <b>YAKURA DONAT</b>\n\n"
        "🎮 O'yinni tanlang.\n"
        "💎 Paketni tanlang.\n"
        "🆔 Player ID kiriting.\n"
        "🚀 Buyurtma avtomatik yuboriladi.",
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================
# GAMES
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data == "games"
)
def games(call):

    try:
        result = g2bulk.get_games()
        games_list = get_list(result)

    except Exception as e:

        logging.exception(e)

        bot.answer_callback_query(
            call.id,
            "O'yinlarni olishda xatolik"
        )
        return

    kb = InlineKeyboardMarkup()

    for game in games_list[:100]:

        code = game_code(game)

        if not code:
            continue

        name = game_name(game)

        kb.add(
            InlineKeyboardButton(
                f"🎮 {name}",
                callback_data=f"game:{code}"
            )
        )

    bot.edit_message_text(
        "🎮 <b>O'YINLAR</b>\n\n"
        "Kerakli o'yinni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================
# GAME
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("game:")
)
def game_selected(call):

    code = call.data.split(":", 1)[1]

    users[call.message.chat.id] = {
        "game_code": code
    }

    try:
        result = g2bulk.catalogue(code)
        products = get_list(result)

    except Exception as e:

        logging.exception(e)

        bot.answer_callback_query(
            call.id,
            "Paketlarni olishda xatolik"
        )
        return

    if not products:

        bot.send_message(
            call.message.chat.id,
            "❌ Bu o'yin uchun paket topilmadi."
        )
        return

    kb = InlineKeyboardMarkup()

    for i, product in enumerate(products[:50]):

        name = product_name(product)
        price = product_price(product)
        sell_price = markup_price(price)

        kb.add(
            InlineKeyboardButton(
                f"{name} — {money(sell_price)}",
                callback_data=f"product:{i}"
            )
        )

    users[call.message.chat.id]["products"] = products

    bot.edit_message_text(
        "📦 <b>PAKETNI TANLANG</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================
# PRODUCT
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("product:")
)
def product_selected(call):

    uid = call.message.chat.id
    index = int(call.data.split(":")[1])

    state = users.get(uid, {})
    products = state.get("products", [])

    if index >= len(products):
        return

    product = products[index]

    state["product"] = product
    state["step"] = "player_id"

    name = product_name(product)
    price = product_price(product)
    sell_price = markup_price(price)

    bot.send_message(
        uid,
        f"📦 <b>{html.escape(name)}</b>\n"
        f"💰 Narx: <b>{money(sell_price)}</b>\n\n"
        f"🆔 Player ID'ingizni yuboring:",
        parse_mode="HTML"
    )


# =========================
# PLAYER ID
# =========================

@bot.message_handler(
    func=lambda m: users.get(m.chat.id, {}).get("step") == "player_id"
)
def player_id(message):

    uid = message.chat.id
    state = users[uid]

    state["player_id"] = message.text.strip()
    state["step"] = "server_id"

    game_code_value = state["game_code"]

    try:
        servers = g2bulk.get_servers(game_code_value)
    except:
        servers = {}

    server_list = get_list(servers)

    if not server_list:

        state["server_id"] = None
        confirm_order(message)
        return

    kb = InlineKeyboardMarkup()

    for server in server_list[:50]:

        sid = str(
            server.get("id")
            or server.get("server_id")
            or server.get("code")
            or ""
        )

        sname = str(
            server.get("name")
            or server.get("title")
            or sid
        )

        if sid:
            kb.add(
                InlineKeyboardButton(
                    sname,
                    callback_data=f"server:{sid}"
                )
            )

    bot.send_message(
        uid,
        "🌐 <b>Serverni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================
# SERVER
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("server:")
)
def server_selected(call):

    uid = call.message.chat.id

    server_id = call.data.split(":", 1)[1]

    users[uid]["server_id"] = server_id

    confirm_order(call.message)


# =========================
# CONFIRM
# =========================

def confirm_order(message):

    uid = message.chat.id
    state = users[uid]

    product = state["product"]

    name = product_name(product)
    cost = product_price(product)
    price = markup_price(cost)

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "💳 To'lov",
            callback_data="pay"
        )
    )

    kb.add(
        InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data="cancel"
        )
    )

    bot.send_message(
        uid,
        f"🛒 <b>BUYURTMA</b>\n\n"
        f"📦 {html.escape(name)}\n"
        f"🆔 {html.escape(state['player_id'])}\n"
        f"💰 <b>{money(price)}</b>\n\n"
        f"Buyurtmani davom ettirasizmi?",
        parse_mode="HTML",
        reply_markup=kb
    )


# =========================
# PAYMENT
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data == "pay"
)
def payment(call):

    uid = call.message.chat.id
    state = users.get(uid)

    if not state:
        return

    product = state["product"]
    price = markup_price(product_price(product))

    state["step"] = "receipt"

    bot.send_message(
        uid,
        f"💳 <b>TO'LOV</b>\n\n"
        f"Karta: <code>{html.escape(CARD_NUMBER)}</code>\n"
        f"Karta egasi: <b>{html.escape(CARD_HOLDER)}</b>\n\n"
        f"💰 Summa: <b>{money(price)}</b>\n\n"
        f"To'lovdan keyin chek rasmini yuboring.",
        parse_mode="HTML"
    )


# =========================
# RECEIPT
# =========================

@bot.message_handler(
    content_types=["photo"]
)
def receipt(message):

    uid = message.chat.id
    state = users.get(uid, {})

    if state.get("step") != "receipt":
        return

    photo = message.photo[-1].file_id

    bot.send_message(
        uid,
        "⏳ To'lov tekshirilmoqda..."
    )

    # Admin uchun buyurtma
    product = state["product"]

    price = markup_price(
        product_price(product)
    )

    admin_text = (
        "📥 <b>YANGI BUYURTMA</b>\n\n"
        f"👤 User ID: <code>{uid}</code>\n"
        f"🎮 Game: <code>{html.escape(state['game_code'])}</code>\n"
        f"📦 Paket: {html.escape(product_name(product))}\n"
        f"🆔 Player: <code>{html.escape(state['player_id'])}</code>\n"
        f"💰 Narx: <b>{money(price)}</b>"
    )

    if ADMIN_ID:
        bot.send_photo(
            ADMIN_ID,
            photo,
            caption=admin_text,
            parse_mode="HTML"
        )

    # Hozircha admin tasdiqlaydi.
    # Keyingi bosqichda avtomatik payment qo'shamiz.

    bot.send_message(
        uid,
        "✅ Chek qabul qilindi.\n\n"
        "Admin to'lovni tasdiqlagach buyurtma G2Bulk'ka yuboriladi."
    )

    users[uid] = {}


# =========================
# CANCEL
# =========================

@bot.callback_query_handler(
    func=lambda c: c.data == "cancel"
)
def cancel(call):

    users.pop(call.message.chat.id, None)

    bot.send_message(
        call.message.chat.id,
        "❌ Buyurtma bekor qilindi.\n\n/start"
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    print("YAKURA G2Bulk started")

    bot.infinity_polling(
        skip_pending=True
        )
