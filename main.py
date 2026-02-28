import os
import json
import random
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 123456789  # حط ايديك هنا

DATA_FILE = "data.json"

# ------------------ DATABASE ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "codes": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ------------------ LANGUAGES ------------------

LANGS = {
    "en": "English",
    "ar": "العربية",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
    "tr": "Türkçe",
    "ru": "Русский"
}

TEXT = {
    "en": {
        "menu": "Main Menu",
        "daily": "🎁 Daily Reward",
        "wheel": "🎰 Spin Wheel (2 pts)",
        "leader": "🏆 Leaderboard",
        "support": "🛠 Support",
        "back": "🔙 Back",
        "points": "Your Points:"
    },
    "ar": {
        "menu": "القائمة الرئيسية",
        "daily": "🎁 هدية يومية",
        "wheel": "🎰 عجلة الحظ (2 نقطة)",
        "leader": "🏆 المتصدرين",
        "support": "🛠 الدعم الفني",
        "back": "🔙 رجوع",
        "points": "نقاطك:"
    }
}

def t(user_id, key):
    lang = data["users"][str(user_id)]["lang"]
    return TEXT.get(lang, TEXT["en"]).get(key, key)

# ------------------ START ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "points": 0,
            "invites": 0,
            "lang": "en",
            "daily": "",
        }
        save_data(data)

    keyboard = [
        [InlineKeyboardButton(v, callback_data=f"lang_{k}")]
        for k, v in LANGS.items()
    ]

    await update.message.reply_text(
        "Choose Language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------ MAIN MENU ------------------

async def main_menu(update: Update, context):
    query = update.callback_query
    uid = str(query.from_user.id)

    keyboard = [
        [InlineKeyboardButton(t(uid, "daily"), callback_data="daily")],
        [InlineKeyboardButton(t(uid, "wheel"), callback_data="wheel")],
        [InlineKeyboardButton(t(uid, "leader"), callback_data="leader")],
        [InlineKeyboardButton(t(uid, "support"), url="https://t.me/netflix_centerBOT")]
    ]

    await query.edit_message_text(
        f"{t(uid, 'menu')}\n\n{t(uid, 'points')} {data['users'][uid]['points']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------ CALLBACK ------------------

async def callbacks(update: Update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    data_cb = query.data

    # Language select
    if data_cb.startswith("lang_"):
        lang = data_cb.split("_")[1]
        data["users"][uid]["lang"] = lang
        save_data(data)
        await main_menu(update, context)

    # Daily reward
    elif data_cb == "daily":
        today = datetime.now().date()
        last = data["users"][uid]["daily"]

        if last == str(today):
            await query.answer("Already claimed today.")
        else:
            data["users"][uid]["points"] += 1
            data["users"][uid]["daily"] = str(today)
            save_data(data)
            await query.answer("You got 1 point!")

        await main_menu(update, context)

    # Wheel
    elif data_cb == "wheel":
        if data["users"][uid]["points"] < 2:
            await query.answer("Not enough points.")
        else:
            data["users"][uid]["points"] -= 2
            reward = random.choice([0,1,2,3,5])
            data["users"][uid]["points"] += reward
            save_data(data)
            await query.answer(f"You won {reward} points!")

        await main_menu(update, context)

    # Leaderboard
    elif data_cb == "leader":
        top = sorted(
            data["users"].items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )[:10]

        text = "🏆 Leaderboard\n\n"
        for i, (u, info) in enumerate(top, 1):
            text += f"{i}. {info['points']} pts\n"

        await query.edit_message_text(text)

# ------------------ CODE SYSTEM ------------------

async def redeem(update: Update, context):
    uid = str(update.effective_user.id)
    if len(context.args) == 0:
        return

    code = context.args[0]

    if code not in data["codes"]:
        await update.message.reply_text("Invalid code.")
        return

    if data["codes"][code]["uses"] >= 2:
        await update.message.reply_text("Code expired.")
        return

    data["users"][uid]["points"] += 2
    data["codes"][code]["uses"] += 1
    save_data(data)

    await update.message.reply_text("You received 2 points!")

# ------------------ ADMIN ------------------

async def broadcast(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    for u in data["users"]:
        try:
            await context.bot.send_message(chat_id=u, text=msg)
        except:
            pass

    await update.message.reply_text("Broadcast sent.")

async def create_code(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    code = context.args[0]
    data["codes"][code] = {"uses": 0}
    save_data(data)

    await update.message.reply_text(f"Code {code} created.")

# ------------------ RUN ------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("redeem", redeem))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("createcode", create_code))
app.add_handler(CallbackQueryHandler(callbacks))

app.run_polling()
