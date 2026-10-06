import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# ⚙️ SOZLAMALAR (O'zingizning ma'lumotlaringizni shu yerga yozing)
# ==========================================
BOT_TOKEN = "BOT_TOKENINGIZNI_SHU_YERGA_YOZING"
ADMIN_ID = 123456789  # O'zingizning Telegram ID raqamingiz (masalan: 123456789)
ADMIN_USERNAME = "@admin_username"  # Telegram username'ingiz (masalan: @shoh_admin)

# Uzum Visa kartangiz ma'lumotlari:
CARD_NUMBER = "4000 0000 0000 0000"  # 16 xonali Uzum Visa karta raqamingiz
CARD_HOLDER = "Ism Familiya"  # Visa kartangizdagi ism-familiyangiz

bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchilar buyurtma holatini saqlash uchun
user_states = {}

# ==========================================
# 🎮 O'YINLAR VA ILOVALAR RO'YXATI
# ==========================================
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
        "title": "🧱 Roblox (Robux)",
        "items": [
            {"id": "r1", "name": "80 Robux", "price": 18000},
            {"id": "r2", "name": "400 Robux", "price": 75000},
            {"id": "r3", "name": "800 Robux", "price": 145000},
        ]
    },
    "brawl_stars": {
        "title": "⭐ Brawl Stars / Supercell",
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

# ==========================================
# 🚀 /START BUYRUG'I
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_states[message.chat.id] = {}
    markup = InlineKeyboardMarkup()
    
    for g_key, g_data in GAMES.items():
        markup.add(InlineKeyboardButton(text=g_data["title"], callback_data=f"game_{g_key}"))
        
    markup.add(InlineKeyboardButton(text="💬 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"))

    text = (
        "⚡️ **夜・YAKURA | Donat Store**\n\n"
        "Xush kelibsiz! Barcha turdagi o'yin va ilovalarga tezkor va xavfsiz donat xizmati.\n\n"
        "👇 Kerakli o'yin yoki bo'limni tanlang:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# ==========================================
# 🔘 TUGMALARNI QABUL QILISH (CALLBACK)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    # 1. O'yin tanlanganda
    if call.data.startswith("game_"):
        game_key = call.data.split("_")[1]
        
        if game_key == "custom":
            user_states[chat_id] = {"game": "Boshqa ilova/o'yin", "step": "wait_custom_details"}
            bot.send_message(
                chat_id, 
                "✍️ **Boshqa o'yin yoki ilova**\n\n"
                "Iltimos, donat qilmoqchi bo'lgan **o'yin/ilova nomi** va qancha/nima xarid qilmoqchiligingizni yozib yuboring:\n"
                "*(Masalan: Telegram Premium 3 oylik yoki FC Mobile 1000 FC Points)*"
            )
            return

        game_data = GAMES[game_key]
        user_states[chat_id] = {"game": game_data["title"]}
        
        markup = InlineKeyboardMarkup()
        for item in game_data["items"]:
            markup.add(InlineKeyboardButton(
                text=f"{item['name']} — {item['price']:,} so'm", 
                callback_data=f"item_{item['id']}_{item['price']}"
            ))
        markup.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"🎮 **{game_data['title']}**\n\nKerakli paketni tanlang:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 2. Paket tanlanganda
    elif call.data.startswith("item_"):
        _, item_id, price = call.data.split("_")
        
        item_name = "Paket"
        for g in GAMES.values():
            for it in g["items"]:
                if it["id"] == item_id:
                    item_name = it["name"]
                    break

        user_states[chat_id]["item_name"] = item_name
        user_states[chat_id]["price"] = int(price)
        user_states[chat_id]["step"] = "wait_game_id"

        bot.send_message(
            chat_id,
            f"✅ Tanlandi: **{user_states[chat_id]['game']} - {item_name}**\n"
            f"💰 Narxi: **{int(price):,} so'm**\n\n"
            f"📝 Endi o'yindagi **ID raqamingizni (yoki nik) / login ma'lumotlaringizni** kiriting:",
            parse_mode="Markdown"
        )

    # 3. Asosiy menyuga qaytish
    elif call.data == "back_to_main":
        start_cmd(call.message)

# ==========================================
# 📩 MATN VA CHEK QABUL QILISH
# ==========================================
@bot.message_handler(content_types=['text', 'photo'])
def handle_messages(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {})

    # 1. Boshqa o'yin nomini yozganda
    if state.get("step") == "wait_custom_details":
        user_states[chat_id]["item_name"] = message.text
        user_states[chat_id]["price"] = "Kelishiladi"
        user_states[chat_id]["step"] = "wait_game_id"
        
        bot.send_message(
            chat_id, 
            "📝 Rahmat! Endi o'yindagi **ID / Login ma'lumotlaringizni** yozib yuboring:"
        )

    # 2. O'yin ID sini yozganda
    elif state.get("step") == "wait_game_id":
        user_states[chat_id]["account_info"] = message.text
        user_states[chat_id]["step"] = "wait_receipt"

        price_text = f"{state['price']:,} so'm" if isinstance(state['price'], int) else state['price']
        
        payment_info = (
            f"💳 **To'lov usuli (Uzum Visa):**\n\n"
            f"Karta raqami: `{CARD_NUMBER}`\n"
            f"Karta egasi: **{CARD_HOLDER}**\n"
            f"To'lov summasi: **{price_text}**\n\n"
            f"⚠️️ To'lovni Uzum yoki boshqa bank ilovasi orqali amalga oshirgach, **to'lov chekini (skrinshot/rasmini)** shu yerga yuboring!"
        )
        bot.send_message(chat_id, payment_info, parse_mode="Markdown")

    # 3. To'lov chekini (rasmini) yuborganda
    elif state.get("step") == "wait_receipt" and message.photo:
        photo_id = message.photo[-1].file_id
        
        bot.send_message(
            chat_id, 
            "✅ **Buyurtmangiz qabul qilindi!**\n"
            "Adminlar to'lovni va ID ma'lumotlarni tekshirib, tez orada donatni o'yiningizga tushirib berishadi."
        )

        price_text = f"{state['price']:,} so'm" if isinstance(state['price'], int) else state['price']
        admin_msg = (
            f"📥 **YANGI BUYURTMA!**\n\n"
            f"👤 **Foydalanuvchi:** @{message.from_user.username or 'Username_yoq'} (ID: `{chat_id}`)\n"
            f"🎮 **O'yin/Ilova:** {state.get('game')}\n"
            f"📦 **Paket:** {state.get('item_name')}\n"
            f"💰 **Narx:** {price_text}\n"
            f"🆔 **Hisob kodi/ID:** `{state.get('account_info')}`\n"
        )
        
        bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, parse_mode="Markdown")
        user_states[chat_id] = {}

    elif state.get("step") == "wait_receipt" and not message.photo:
        bot.send_message(chat_id, "⚠️ Iltimos, to'lov amalga oshirilgan **rasm/chek (skrinshot)** yuboring.")

if __name__ == '__main__':
    print("YAKURA Bot muvaffaqiyatli ishga tushdi...")
    bot.polling(none_stop=True)
  
