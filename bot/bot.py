import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =============================================
#   SOZLAMALAR
# =============================================
BOT_TOKEN    = "8397197387:AAEVpZgpakEwLKHnSa9NHk1IYSSsH7wgAeo"
ADMIN_ID     = 397162553
CHANNEL_ID   = "@tarjima_kinolar_uzbek123"
CHANNEL_LINK = "https://t.me/tarjima_kinolar_uzbek123"
CHANNEL_LINK1 = "https://t.me/+--3JIi79uoY2NjZi"
CHANNEL_LINK2 = "https://t.me/+_f1z1kMvZ6gzNWVi"
DB_FILE      = "movies.json"
# =============================================

bot = telebot.TeleBot(BOT_TOKEN)
admin_state = {}


# ─── Ma'lumotlar bazasi ───────────────────────────────────────────────────────

def load_movies() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_movies(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record_view(code: str, user_id: int):
    """Kino ko'rilganda statistika yangilanadi."""
    movies = load_movies()
    if code not in movies:
        return
    movie = movies[code]
    movie.setdefault("views", 0)
    movie.setdefault("viewers", [])
    movie["views"] += 1
    if user_id not in movie["viewers"]:
        movie["viewers"].append(user_id)
    save_movies(movies)


# ─── Yordamchi funksiyalar ────────────────────────────────────────────────────

def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID

def is_subscribed(uid: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_ID, uid)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"[XATO] obuna: {e}")
        return False


# ─── Klaviaturalar ────────────────────────────────────────────────────────────

def admin_panel_kb() -> InlineKeyboardMarkup:
    """Admin uchun asosiy panel tugmalari."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Kino qo'shish",  callback_data="adm_add"),
        InlineKeyboardButton("📋 Ro'yxat",         callback_data="adm_list"),
    )
    kb.add(
        InlineKeyboardButton("🗑 O'chirish",        callback_data="adm_delete"),
        InlineKeyboardButton("📊 Statistika",       callback_data="adm_stats"),
    )
    return kb

def sub_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=CHANNEL_LINK))
    kb.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=CHANNEL_LINK1))
    kb.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=CHANNEL_LINK2))
    kb.add(InlineKeyboardButton("✅ Obunani tekshirish",    callback_data="check_sub"))
    return kb

def cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_add"))
    return kb

def back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Admin panel", callback_data="adm_home"))
    return kb


# ─── /start ──────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id

    if is_admin(uid):
        bot.send_message(
            uid,
            "👑 <b>Admin paneliga xush kelibsiz!</b>\n\n"
            "Quyidagi tugmalardan foydalaning:",
            parse_mode="HTML",
            reply_markup=admin_panel_kb(),
        )
        return

    name = message.from_user.first_name
    if is_subscribed(uid):
        bot.send_message(
            uid,
            f"👋 Salom, <b>{name}</b>!\n\n"
            "🎬 Kino kodini yuboring va filmni oling.",
            parse_mode="HTML",
        )
    else:
        bot.send_message(
            uid,
            f"👋 Salom, <b>{name}</b>!\n\n"
            "⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling.\n\n"
            "✅ Obuna bo'lgach <b>«Obunani tekshirish»</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=sub_kb(),
        )


# ─── Callback tugmalar ────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    uid  = call.from_user.id
    data = call.data

    # ── Foydalanuvchi: obuna tekshirish
    if data == "check_sub":
        if is_subscribed(uid):
            bot.edit_message_text(
                "✅ <b>Obuna tasdiqlandi!</b>\n\n"
                "🎬 Endi kino kodini yuboring.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
            )
        else:
            bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)
        return

    # ── Faqat admin uchun
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q.", show_alert=True)
        return

    # ── Admin: bosh panel
    if data == "adm_home":
        bot.edit_message_text(
            "👑 <b>Admin paneli</b>\n\nQuyidagi tugmalardan foydalaning:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=admin_panel_kb(),
        )

    # ── Admin: kino qo'shish
    elif data == "adm_add":
        admin_state[uid] = {"step": "wait_video"}
        bot.edit_message_text(
            "🎬 <b>1-qadam:</b> Kino faylini yuboring.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=cancel_kb(),
        )

    # ── Admin: ro'yxat
    elif data == "adm_list":
        movies = load_movies()
        if not movies:
            bot.answer_callback_query(call.id, "📭 Hozircha hech qanday kino yo'q.", show_alert=True)
            return
        text = "📋 <b>Kinolar ro'yxati:</b>\n\n"
        for code, info in movies.items():
            views   = info.get("views", 0)
            viewers = len(info.get("viewers", []))
            text += f"🎬 Kod: <code>{code}</code>  |  👁 {views} marta  |  👤 {viewers} kishi\n"
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=back_kb(),
        )

    # ── Admin: o'chirish
    elif data == "adm_delete":
        movies = load_movies()
        if not movies:
            bot.answer_callback_query(call.id, "📭 O'chiriladigan kino yo'q.", show_alert=True)
            return
        kb = InlineKeyboardMarkup()
        for code in movies:
            kb.add(InlineKeyboardButton(f"🗑 {code}", callback_data=f"del_{code}"))
        kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="adm_home"))
        bot.edit_message_text(
            "🗑 <b>Qaysi kinoni o'chirmoqchisiz?</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )

    # ── Admin: statistika — kinolar ro'yxati
    elif data == "adm_stats":
        movies = load_movies()
        if not movies:
            bot.answer_callback_query(call.id, "📭 Hozircha hech qanday kino yo'q.", show_alert=True)
            return
        kb = InlineKeyboardMarkup()
        for code in movies:
            kb.add(InlineKeyboardButton(f"🎬 {code}", callback_data=f"stat_{code}"))
        kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="adm_home"))
        bot.edit_message_text(
            "📊 <b>Statistika</b>\n\nQaysi kinoning statistikasini ko'rmoqchisiz?",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )

    # ── Admin: bitta kino statistikasi
    elif data.startswith("stat_"):
        code   = data[5:]
        movies = load_movies()
        movie  = movies.get(code)
        if not movie:
            bot.answer_callback_query(call.id, "Kino topilmadi.", show_alert=True)
            return
        views   = movie.get("views", 0)
        viewers = len(movie.get("viewers", []))
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Statistikaga qaytish", callback_data="adm_stats"))
        bot.edit_message_text(
            f"📊 <b>Statistika — kod: {code}</b>\n\n"
            f"👁  Ko'rishlar soni:  <b>{views}</b> marta\n"
            f"👤 Noyob tomoshabinlar: <b>{viewers}</b> kishi",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
        )

    # ── Admin: kino o'chirishni tasdiqlash
    elif data.startswith("del_"):
        code   = data[4:]
        movies = load_movies()
        if code in movies:
            del movies[code]
            save_movies(movies)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔙 Admin panel", callback_data="adm_home"))
            bot.edit_message_text(
                f"🗑 <b>{code}</b> kodli kino o'chirildi.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
            bot.answer_callback_query(call.id, "Kino topilmadi.", show_alert=True)

    # ── Bekor qilish
    elif data == "cancel_add":
        admin_state.pop(uid, None)
        bot.edit_message_text(
            "❌ Amal bekor qilindi.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=back_kb(),
        )


# ─── Video qabul qilish ───────────────────────────────────────────────────────

@bot.message_handler(content_types=["video", "document"])
def handle_video(message):
    uid = message.from_user.id
    if not is_admin(uid):
        return
    state = admin_state.get(uid, {})
    if state.get("step") != "wait_video":
        return

    file_id = message.video.file_id if message.video else message.document.file_id
    admin_state[uid] = {"step": "wait_code", "file_id": file_id}
    bot.send_message(
        uid,
        "✅ Kino qabul qilindi!\n\n"
        "🔢 <b>2-qadam:</b> Endi bu kinoning <b>kodini</b> yuboring.\n"
        "Masalan: <code>001</code>",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


# ─── Matn xabarlari ───────────────────────────────────────────────────────────

@bot.message_handler(content_types=["text"])
def handle_text(message):
    uid  = message.from_user.id
    text = message.text.strip()

    # ── Admin: kod kutilmoqda
    if is_admin(uid):
        state = admin_state.get(uid, {})
        if state.get("step") == "wait_code":
            code   = text
            movies = load_movies()
            if code in movies:
                bot.send_message(
                    uid,
                    f"⚠️ <b>{code}</b> kodi allaqachon mavjud.\n"
                    "Boshqa kod kiriting.",
                    parse_mode="HTML",
                    reply_markup=cancel_kb(),
                )
                return
            movies[code] = {
                "file_id": state["file_id"],
                "views":   0,
                "viewers": [],
            }
            save_movies(movies)
            admin_state.pop(uid, None)
            bot.send_message(
                uid,
                f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
                f"📌 Kod: <code>{code}</code>",
                parse_mode="HTML",
                reply_markup=admin_panel_kb(),
            )
            return

        # Admin boshqa matn — panelni qayta ko'rsat
        bot.send_message(
            uid,
            "👑 <b>Admin paneli</b>",
            parse_mode="HTML",
            reply_markup=admin_panel_kb(),
        )
        return

    # ── Foydalanuvchi: obuna tekshiruvi
    if not is_subscribed(uid):
        bot.send_message(uid, "⚠️ Kino olish uchun avval kanalga obuna bo'ling!", reply_markup=sub_kb())
        return

    # ── Foydalanuvchi: kino kodi
    movies = load_movies()
    movie  = movies.get(text)
    if not movie:
        bot.send_message(
            uid,
            f"❌ <b>{text}</b> kodli kino topilmadi.\nTo'g'ri kodni kiriting.",
            parse_mode="HTML",
        )
        return

    wait = bot.send_message(uid, "⏳ Kino yuklanmoqda...")
    try:
        bot.delete_message(uid, wait.message_id)
        bot.send_video(
            uid,
            video=movie["file_id"],
            caption=f"🎬 Kino kodi: <b>{text}</b>",
            parse_mode="HTML",
        )
        record_view(text, uid)
    except Exception as e:
        print(f"[XATO] video yuborish: {e}")
        bot.send_message(uid, "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")


# ─── Ishga tushirish ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("✅ Bot ishga tushdi...")
    bot.infinity_polling()
